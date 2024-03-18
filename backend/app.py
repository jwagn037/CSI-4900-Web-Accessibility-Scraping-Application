################################### IMPORTS ###################################
from flask import Flask, request, g, render_template
import psycopg2 # Docs: https://www.psycopg.org/docs/usage.html
import wasa_db_handler
import requests
from bs4 import BeautifulSoup
from trafilatura import extract
import validators
import base64
from PIL import Image
from io import BytesIO

# import domain_parser

################################### FLASK ###################################

app = Flask(__name__)

@app.before_request 
def before_request():
    # Connect to the database:
    conn = psycopg2.connect(
         host="localhost",
         database="WASA_db",
         user='WASA_admin',
         password='admin')
    g.cur = conn.cursor()
    g.db = conn
    # Build our adserver, allowlist, blocklist dictionaries:
    # adserver_dict = domain_parser.get_domain_dict("adservers")
    # blocklist_dict = domain_parser.get_domain_dict("blocklist")
    # allowlist_dict = domain_parser.get_domain_dict("allowlist")
   
@app.after_request
def after_request(response):
    # Close the database connection
    if g.db is not None:
        print('closing connection')
        g.db.commit()
        g.cur.close()
        g.db.close()
    
    # CORS-ish: https://stackoverflow.com/questions/19962699/flask-restful-cross-domain-issue-with-angular-put-options-methods
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET')
    return response

@app.get('/') # index root
def index():
    return "WASA API up."

@app.get('/admin/') # admin panel
def admin():
    return render_template("admin.html")

@app.get('/url')
def scrape_url():
    # API mode options.
    parse_mode = 1 # There are many ways to parse HTML. See parse_reponse() function header for information.
    # Check for valid request
    if request.method != 'GET':
        return "Invalid request"
    # Get arguments
    url, get_images, generate_alt_text = None, True, False
    args = request.args
    print("ARGS",args)
    if (len(args) > 0):
        url = args.get("url")
    if ("get_images" in args):
        if (str(args.get("get_images")) in ('true','True','1')):
            get_images = True
        else:
            get_images = False
    if ("generate_alt_text" in args):
        if (str(args.get("generate_alt_text")) in ('true','True','1')):
            generate_alt_text = True
        else:
            generate_alt_text = False
    if (len(args) == 0 or len(args) > 3):
        print("Caller supplied too many arguments to the API.")
        return "Caller supplied too many arguments to the API."
    print("CALLER SUBMITTED: ", url, get_images, generate_alt_text)
    
    # check that the requested URL is valid
    # validators: https://pypi.org/project/validators/
    if (validators.url(url) == False):
        return "Invalid URL"
    
    # Try to read from cache
    cache_json = wasa_db_handler.read_cache_request(url)
    
    if (cache_json == False):
        print("Read FAILURE: ", url)
    
        # Can't read from cache. Make request.
        print("Requesting HTML:", url)
        response = requests.get(url)
        html = response.text
        
        if response.status_code == 200:
            print("Parsing HTML:",url)
            response_json = parse_response(html, parse_mode)
            print("Saving JSON:",url)
            wasa_db_handler.write_cache_request(url, response_json)
        else:
            print("Save FAILURE: Invalid status_code:", response.status_code)
        return json_linter(response_json)
    print("Returning from cache.")
    return json_linter(cache_json)

# @app.get('/url')
# def scrape_url():
#     # API mode options.
#     parse_mode = 1 # There are many ways to parse HTML. See parse_reponse() function header for information.
#     # Check for valid request
#     if request.method != 'GET':
#         return "Invalid request"
    
#     url = str(request.args.get('data'))
#     print("GET: ", url, "(this does not make a request)")
    
#     # check that the requested URL is valid
#     # validators: https://pypi.org/project/validators/
#     if (validators.url(url) == False):
#         return "Invalid URL"
    
#     # Try to read from cache
#     cache_json = wasa_db_handler.read_cache_request(url)
    
#     if (cache_json == False):
#         print("Read FAILURE: ", url)
    
#         # Can't read from cache. Make request.
#         print("Requesting HTML:", url)
#         response = requests.get(url)
#         html = response.text
        
#         if response.status_code == 200:
#             print("Parsing HTML:",url)
#             response_json = parse_response(html, parse_mode)
#             print("Saving JSON:",url)
#             wasa_db_handler.write_cache_request(url, response_json)
#         else:
#             print("Save FAILURE: Invalid status_code:", response.status_code)
#         return json_linter(response_json)
#     print("Returning from cache.")
#     return json_linter(cache_json)
    


################################### FUNCTIONS ###################################
    
    # Handles complex business logic for different HTML parsing approaches.
    # mode == 0: BS4 parsing
    # mode == 1: Trafilatura parsing
    # Defaults to an empty response.
def parse_response(html, parse_mode=0):
    json_default = "{}" ## default empty JSON
    
    # minimal parsing:
    tags = ['h1','h2','h3','h4','h5','h6', 'p', 'ul', 'img', 'caption', 'figcaption']
    soup = BeautifulSoup(html, 'html.parser')
    result = soup.find_all(tags)
    
    if (parse_mode == 0): #BS4 parsing ... technically already done above, since we use these results to do our other parsing
        return write_json(result)
    
    elif (parse_mode == 1): # Trafilatura parsing
        soup.findAll(text=True)
        text = extract(html, favor_precision=True, include_images=True)
        for item in result:            
            if (item.text not in text):
                result.remove(item)
        return write_json(result)
    return json_default

    # Builds a JSON object with the format provided in the wiki.
    # Needs a ResultSet for text. The rest can be blank, or strings.
def write_json(text, title='',author='',date=''):
    json_article = {}
    json_article['title'] = title
    json_article['author'] = author
    json_article['date'] = date
    content = []
    
    for item in text:
        item_json ={}
        if (item.name == "img"): # Image element
            item_json['text'] = img_src_to_b64(item.get('src'))
            if (item_json['text'] == False):
                continue
            
            item_json['type'] = "img"
            item_json['caption'] = ''
            
            if (item.get('alt') is None):
                item_json['alt_text'] = ''
            else:
                item_json['alt_text'] = item.get('alt')
            item_json['alt_text_type'] = "original"
            content.append(item_json)
        else: # Textual element
            item_json['type'] = item.name
            item_json['text'] = item.text
            content.append(item_json)
        
    json_article['content'] = content
    return json_article

# Takes an image src and tries to convert it to base 64.
# Returns a base 64 string on a success, or False on a failure.
def img_src_to_b64(src):
    try:
        response = requests.get(src)
        if response.status_code == 200:
            image_content = response.content
            base64_img = base64.b64encode(image_content).decode('utf-8')
            return base64_img
        else:
            return False
    except Exception as e:
        # print("Error:", e) # This isn't necessarily an error. If the image can't be encoded, then it was probably malformed when we scraped it.
        return False

def json_linter(json):
    json_article = {}
    json_article['title'] = json['title']
    json_article['author'] = json['author']
    json_article['date'] = json['date']
    content = []
    headline_flag = False
    
    for item in json['content']:
        item_json ={}
        if (item['type'] == 'h1'):
            headline_flag = True
        if (item['type'] != "img"):
            if (headline_flag): # Chop off everything before the first headline
                item_json['type'] = item['type']
                item_json['text'] = item['text']
        else: # WAPI uses heuristics in a function to decide whether to include an image
            if (include_image(item)):
                item_json['type'] = item['type']
                item_json['text'] = item['text']
                item_json['alt_text'] = item['alt_text']
                item_json['alt_text_type'] = item['alt_text_type']
                item_json['caption'] = ''
            else:
                continue
        content.append(item_json)
        
    json_article['content'] = content
    return json_article


# Takes a base64 image. Returns True if the image
# passes some heuristics. False if it does not.
def include_image(image_element):
    data = image_element['text']
    include = True
    
    img = base64.b64decode(data)
    image = Image.open(BytesIO(img))
    
    width, height = image.size
    pixels = width*height
    aspect_ratio = width / height
    
    if (pixels < 120000): # Heuristic from [14]: https://dl-acm-org.proxy.bib.uottawa.ca/doi/pdf/10.1145%2F3616849
        include = False
        
    if (width < 700):
        include = False
        
    if (height < 400):
        include = False
        
    if (aspect_ratio < 1.0):
        include = False
    
    return include
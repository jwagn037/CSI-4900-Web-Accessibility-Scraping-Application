################################### IMPORTS ###################################
from flask import Flask, request, g, render_template
import psycopg2
import requests
from bs4 import BeautifulSoup
from trafilatura import extract
import validators
import base64
from PIL import Image
from io import BytesIO
import random
import json
import wasa_db_handler
from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.ai.vision.imageanalysis.models import VisualFeatures
from azure.core.credentials import AzureKeyCredential

################################### FLASK ###################################
app = Flask(__name__)

@app.before_request 
def before_request():
    # Generate a random request ID to attach to each print message
    g.RID = "RID#" + str(random.randint(1,100000)) + ":"

    # Connect to the database:
    try:
        print(g.RID, "Reading Postgres credentials.")
        with open("./credentials/postgres_creds.json", "r") as read_file:
            data = json.load(read_file)
        conn = psycopg2.connect(
            host=data['host'],
            database=data['database'],
            user=data['user'],
            password=data['password'])
        g.cur = conn.cursor()
        g.db = conn
    except KeyError:
        print(g.RID, "Error reading Azure Vision credentials.")

    # Connect to Azure Vision
    try:
        print(g.RID,"Reading Azure Vision credentials.")
        with open("./credentials/azure_vision_creds.json", "r") as read_file:
            data = json.load(read_file)
            g.azure_vision_endpoint = data['endpoint']
            g.azure_vision_key = data['key']
    except KeyError:
        print(g.RID,"Error reading Azure Vision credentials.")
    # Build our adserver, allowlist, blocklist dictionaries:
    # adserver_dict = domain_parser.get_domain_dict("adservers")
    # blocklist_dict = domain_parser.get_domain_dict("blocklist")
    # allowlist_dict = domain_parser.get_domain_dict("allowlist")
   
@app.after_request
def after_request(response):
    # Close the database connection
    if g.db is not None:
        print(g.RID, "Closing database connection.")
        g.db.commit()
        g.cur.close()
        g.db.close()
    
    # CORS-ish: https://stackoverflow.com/questions/19962699/flask-restful-cross-domain-issue-with-angular-put-options-methods
    # In the real world, this API would instead be behind a webserver configured to act as a reverse-proxy connected with the frontend.
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
    url, get_images, generate_alt_text = None, True, True

    print(g.RID, "User made a new request.")
    # Check for valid request
    if request.method != 'GET':
        print(g.RID, "Not a get request. Exiting.")
        return "Invalid request"
    # Get arguments
    print(g.RID, "Getting caller-provided arguments for url, get_images, and generate_alt_text.")
    args = request.args
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
        print(g.RID, "Error: expected 3 arguments, got:",len(args))
        return "Expected 3 arguments, got:",len(args)
    print(g.RID, "Caller submitted the following arguments. \n\turl=", url, "\n\tget_images=", get_images, "\n\tgenerate_alt_text=", generate_alt_text)
    
    # check that the requested URL is valid
    if (validators.domain(url) == False):
        print(g.RID, "Error: Supplied url is a bad domain.")
        return "Error: Supplied url is a bad domain."
    else:
        print(g.RID, "Supplied url is a good domain.")
    if (validators.url(url) == False):
        print(g.RID, "Error: Supplied url is a bad url.")
        return "Error: Suppled url is a bad url."
    else:
        print(g.RID, "Supplied url is a good url.")
    
    # Try to read from cache
    print(g.RID, "Reading data from cache.")
    cache_json = wasa_db_handler.read_cache_request(url)
    
    if (cache_json == False):
        print(g.RID, "Read from cache failed. Either this url is not cached, or the database failed.")
        response = requests.get(url)
        html = response.text
        
        if response.status_code == 200:
            print(g.RID, "Request succesful.")
            print(g.RID, "Parsing HTML.")
            response_json = parse_response(html)
            print(g.RID, "Parsing finished.")
            print(g.RID, "Saving JSON for url=",url)
            print(g.RID, "^DISREGARD PREVIOUS LINE; DISABLED SAVE. cache_json=False hardcoded^")
            wasa_db_handler.write_cache_request(url, response_json)
        else:
            print(g.RID, "The request failed with status code=", response.status_code)
            return ''
        print(g.RID, "Returning data. A request was made to the target url for this transaction. The data has been saved for future requests.")
        # return response_json
        return json_linter(response_json, get_images, generate_alt_text)
    print(g.RID, "Read from cache succeeded.")
    print(g.RID, "Returning cached data. No requests were made to the target url for this transaction.")
    return json_linter(cache_json, get_images, generate_alt_text)

################################### FUNCTIONS ###################################
    
    # Handles business logic for parsing an html response using Trafilatura.
    # Returns a JSON-like dictionary
def parse_response(html):
    print(g.RID,"Start parsing")
    tags = ['h1','h2','h3','h4','h5','h6', 'p', 'ul', 'img', 'caption', 'figcaption']
    soup = BeautifulSoup(html, 'html.parser')
    result = soup.find_all(tags)
    get_images, generate_alt_text = True, True # These serve no true purpose except as troubleshooting toggles
    json_article = {}
    json_article['title'] = webpage_title = '' # Not supported yet
    json_article['author'] = webpage_author = '' # Not supported yet
    json_article['date'] = webpage_date = '' # Not supported yet
    content = []
    headline_flag = False

    print(g.RID,"Constructing JSON from request")
    soup.findAll(text=True)
    text = extract(html, favor_precision=True, include_images=True) # Trafilatura
    for element in result: # type(element)=bs4.element.Tag
        # Skip element if it isn't in the ResultSet of BS4 and Trafilatura
        if (element.text not in text): 
            continue

        # Skip everything before the first h1 tag
        if (element.name == 'h1'):
            headline_flag = True
        if (headline_flag == False): 
            continue

        element_content = {}
        # Textual elements: record as-is
        if (element.name != "img" and len(element.text)>0):
            element_content['type'] = element.name
            element_content['text'] = element.text
        # Images: scrutinize ("should we include this image?") and parse (img -> b64).
        elif (get_images):
            element_content['text'] = img_src_to_b64(element.get('src'))
            if (include_image(element_content['text']) == False):
                continue
            element_content['type'] = 'img'
            element_content['caption'] = ''
            if(generate_alt_text and len(element.get('alt')) == 0):
                print(g.RID, "Generating alt-text")
                element_content['alt_text_type'] = 'generated'
                element_content['alt_text'] = generate_alt_text_from_b64(element_content['text'])
            elif len(element.get('alt')) > 0:
                print(g.RID, "Ripping included alt-text")
                element_content['alt_text_type'] = 'original'
                element_content['alt_text'] = element.get('alt')
            else:
                continue
        else:
            continue
        content.append(element_content)
    
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

def generate_alt_text_from_b64(image):
    generated_alt_text = "Default generated alt-text"

    try:
        img = base64.b64decode(image)
        image = BytesIO(img)
    except:
        return generated_alt_text # Something has gone wrong: we can't read this image.
    
    # Create an Image Analysis client for synchronous operations
    client = ImageAnalysisClient(
        endpoint=g.azure_vision_endpoint,
        credential=AzureKeyCredential(g.azure_vision_key)
    )

    # Get a caption for the image. This will be a synchronously (blocking) call.
    result = client.analyze(
        image_data=image,
        visual_features=[VisualFeatures.CAPTION],
    )

    if result.caption is not None:
        generated_alt_text = result.caption.text

    # update the cache
    return generated_alt_text  # update the cache. We don't want to do the work of generating alt-text again.

def json_linter(json, get_images, generate_alt_text):
    print(g.RID,"Start linting")
    content = []
    for element in json['content']:
        if (element['type'] == 'img'):
            if (get_images==False):
                continue
            if (element['alt_text_type'] == 'generated' and generate_alt_text==False):
                continue
        else:
            pass
        content.append(element)
    json['content'] = content
    print(g.RID,"Linting finished")
    return json

# Takes a base64 image. Returns True if the image
# passes some heuristics. False if it does not.
def include_image(image_element):
    include = True

    try:
        img = base64.b64decode(image_element)
        image = Image.open(BytesIO(img))
    except:
        return False # If we can't examine the image, we shouldn't return it.
    
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
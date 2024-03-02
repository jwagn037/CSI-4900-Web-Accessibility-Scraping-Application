################################### IMPORTS ###################################
from flask import Flask, request, g
import psycopg2 # Docs: https://www.psycopg.org/docs/usage.html
import wasa_db_handler
import requests
from bs4 import BeautifulSoup
from trafilatura import extract
import validators
import domain_parser


################################### FLASK ###################################

app = Flask(__name__)

@app.before_request 
def before_request():
    # Connect to the database:
    conn = psycopg2.connect(
         host="localhost",
         database="WASA_DB",
         user='WASA_admin',
         password='admin')
    g.cur = conn.cursor()
    g.db = conn
    # Build our adserver, allowlist, blocklist dictionaries:
    adserver_dict = domain_parser.get_domain_dict("adservers")
    blocklist_dict = domain_parser.get_domain_dict("blocklist")
    allowlist_dict = domain_parser.get_domain_dict("allowlist")
   
@app.after_request
def after_request(response):
    # Close the database connection
    if g.db is not None:
        print('closing connection')
        g.db.commit()
        g.cur.close()
        g.db.close()
    return response

@app.get('/') # index root
def index():
    return "WASA API up."

@app.get('/url')
def scrape_url():
    # API mode options.
    parse_mode = 1 # There are many ways to parse HTML. See parse_reponse() function header for information.
    
    # Check for valid request
    if request.method != 'GET':
        return "Invalid request"
    
    url = str(request.args.get('data'))
    print("GET: ", url)
    
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
        
        return response_json
    
    return cache_json
    
# CORS-ish: https://stackoverflow.com/questions/19962699/flask-restful-cross-domain-issue-with-angular-put-options-methods
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET')
    return response

################################### FUNCTIONS ###################################
    
    # Handles complex business logic for different HTML parsing approaches.
    # mode == 0: BS4 parsing
    # mode == 1: Trafilatura parsing
    # Defaults to BS4 parsing.
def parse_response(html, parse_mode=0):
    json_default = "{}" ## default empty JSON
    
    # minimal parsing:
    tags = ['h1','h2','h3','h4','h5','h6', 'p', 'ul']
    soup = BeautifulSoup(html, 'html.parser')
    result = soup.find_all(tags)
    print(type(result))
    
    if (parse_mode == 0): #BS4 parsing ... technically already done above, since we use these results to do our other parsing
        return write_json(result)
    
    elif (parse_mode == 1): # Trafilatura parsing
        print("MODE 1")
        soup.findAll(text=True)
        text = extract(html, favor_precision=True)
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
        item_json['type'] = item.name
        item_json['text'] = item.text
        content.append(item_json)
        
    json_article['content'] = content
    return json_article
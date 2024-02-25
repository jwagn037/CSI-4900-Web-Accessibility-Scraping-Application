################################### IMPORTS ###################################
from flask import Flask, request
import requests
from bs4 import BeautifulSoup
from trafilatura import extract
import validators
import hashlib
import os


################################### FLASK ###################################

app = Flask(__name__)

@app.get('/') # index root
def index():
    return "WASA API up."

@app.get('/url')
def scrape_url():
    # API mode options.
    parse_mode = 1 # There are many ways to parse HTML. See parse_reponse() function header for information.
    cache_directory = "pseudocache"
    
    # Check for valid request
    if request.method != 'GET':
        return "Invalid request"
    
    url = str(request.args.get('data'))
    print("GET: ", url)
    
    # check that the requested URL is valid
    # validators: https://pypi.org/project/validators/
    if (validators.url(url) == False):
        return "Invalid URL"
    
    # get_url_html is a helper function handling HTML retrieval. See function header for information.
    http = get_url_html(url, directory=cache_directory)
    
    # parse response, get html
    try:
        print("Start parsing.")
        return parse_response(http, parse_mode=parse_mode)
    except Exception as e:
        print("Start parse FAILURE.", str(e))
        return f'An error occurred: {str(e)}'

# CORS-ish: https://stackoverflow.com/questions/19962699/flask-restful-cross-domain-issue-with-angular-put-options-methods
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET')
    return response

################################### FUNCTIONS ###################################

# Handles the complex business logic of getting HTML from a URL.
# Returns HTML. Variable html.type()=str().
def get_url_html(url, directory='pseudocache'):
    os.makedirs(directory, exist_ok=True)  # Create the directory if it doesn't exist
    html_path = os.path.join(directory, hashlib.sha256(url.encode()).hexdigest()) # this is where we will read/save in the cache
    
    # Try to read from cache
    try:
        with open(html_path, 'r', encoding='utf-8') as file:
            print("Reading:", html_path)
            http = file.read()
            print("Read success:", html_path)
            return str(http)
    except Exception as e:
        print("Read FAILURE:", html_path)
    
    # Can't read from cache. Make request.
    print("Request:", url)
    response = requests.get(url)
    html = response.text
    
    if response.status_code == 200:
        with open(html_path, mode='w', encoding='utf-8') as localfile:
            print("Saving:", html_path)
            localfile.write(html)
            print("Save success:", html_path)
    else:
        print("Save FAILURE: Invalid status_code:", response.status_code)
    
    return str(html)
    
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
    json_article['author'] = title
    json_article['date'] = title
    content = []
    
    for item in text:
        item_json ={}
        item_json['type'] = item.name
        item_json['text'] = item.text
        content.append(item_json)
        
    json_article['content'] = content
    return json_article


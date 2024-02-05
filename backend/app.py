from flask import Flask, request
import requests
from bs4 import BeautifulSoup
from trafilatura import extract
import validators
import hashlib
import os

app = Flask(__name__)

@app.get('/') # index root
def index():
    return "WASA API up."

@app.get('/url')
def scrape_url():
    
    # Check for valid request
    if request.method != 'GET':
        return "Invalid request"
    
    url = str(request.args.get('data'))
    print("GET request for: ", url)
    
    # check that the requested URL is valid
    # validators: https://pypi.org/project/validators/
    if (validators.url(url) == False):
        return "Invalid URL"
    
    # check if we have this URL HTML cached
    if in_cache(url):
        http = in_cache(url)
    else:
        http = save_to_cache(url)
    
    # parse response, get html
    try:
        return parse_response(http, mode=0)
    except Exception as e:
        return f'An error occurred: {str(e)}'
    
    # Saves an HTTP response to the pseudocache.
def save_to_cache(url):
    directory = 'pseudocache'
    # use SHA-256 hash to create a unique filename
    filename = os.path.join(directory, hashlib.sha256(url.encode()).hexdigest())
    
    response = requests.get(url)
    http = response.text
    
    os.makedirs(directory, exist_ok=True)  # Create the directory if it doesn't exist
    
    if response.status_code == 200:
        with open(filename, mode='w', encoding='utf-8') as localfile:
            print("Saving "+ filename)
            localfile.write(http)
    
    return http

    # Reads the pseudocache. Returns False if a provided URL does not
    # correpond to a file there, OR a soup if we saved it already.
    # Just exists to reduce the number of queries we make to websites.
    # Anything else is impolite.
def in_cache(url):
    directory = 'pseudocache'
    # use SHA-256 hash to create a unique filename
    filename = os.path.join(directory, hashlib.sha256(url.encode()).hexdigest())
    
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            print("Reading " + filename)
            http = file.read()
            return http
    except Exception as e:
        print(e)
        return False
    
    # mode == 0: BS4 parsing
    # mode == 1: Trafilatura parsing
def parse_response(http, mode):
    json_article = "\{\}"
    
    if (mode == 0):
        soup = BeautifulSoup(http, 'html.parser')
        result_set = parse_soup(soup)
        json_article = write_json(result_set)
    elif (mode == 1):
        pass

    return json_article

    # Parses soup using Beautiful Soup 4.
    # Takes a naive approach by just grabing headers and paragraphs.
    # Returns ResultSet.
def parse_soup(soup):
    tags = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6',  'p']
    text = soup.find_all(tags)
    return text

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

# CORS-ish: https://stackoverflow.com/questions/19962699/flask-restful-cross-domain-issue-with-angular-put-options-methods
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET')
    return response
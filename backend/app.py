from flask import Flask, request, render_template
import requests
from bs4 import BeautifulSoup
import validators
import hashlib
import os

app = Flask(__name__)

@app.route('/') # index root
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit_data():
    # parse URL from submission, get response
    try:
        if request.method == 'POST':
            url = request.form['data']
            if validators.url(url): # check that the requested url is valid
                find_in_cache = in_cache(url)
                if find_in_cache == False:
                    http = save_to_cache(url)
                else:
                    http = find_in_cache
            else:
                return 'URL is invalid'
        else:
            return 'Invalid request method'
    except Exception as e:
        return f'An error occurred: {str(e)}'
    
    # parse response, get html
    try:
        soup = BeautifulSoup(http, 'html.parser')
        return soup.prettify()
    except Exception as e:
        return f'An error occurred: {str(e)}'

if __name__ == "__main__":
    app.run(debug=True) # this should be False in a prod environment
    
    # Saves an HTTP response to the pseudocache.
def save_to_cache(url):
    directory = 'pseudocache'
    # use SHA-256 hash to create a unique filename
    filename = os.path.join(directory, hashlib.sha256(url.encode()).hexdigest())
    
    response = requests.get(url)
    http = response.text
    
    os.makedirs(directory, exist_ok=True)  # Create the directory if it doesn't exist
    
    if response.status_code == 200:
        with open(filename, mode='w') as localfile:
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
        with open(filename, 'r') as file:
            print("Reading " + filename)
            http = file.read()
            return http
    except Exception as e:
        print(e)
        return False

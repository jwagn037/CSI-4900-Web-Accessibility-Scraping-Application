from flask import Flask, request, render_template
import requests
from bs4 import BeautifulSoup
import validators

app = Flask(__name__)

@app.route('/') # index root
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit_data():
    # parse URL from submission, get response
    try:
        if request.method == 'POST':
            if validators.url(url): # check that the requested url is valid
                url = request.form['data']
                response = requests.get(url)
            else:
                return 'URL is invalid'
        else:
            return 'Invalid request method'
    except Exception as e:
        return f'An error occurred: {str(e)}'
    
    # parse response, get html
    try:
        if response.status_code == 200:
            http = response.text
            soup = BeautifulSoup(http, 'html.parser')
        return soup.prettify()
    except Exception as e:
        return f'An error occurred: {str(e)}'

if __name__ == "__main__":
    app.run(debug=True) # this should be False in a prod environment
from flask import Flask, request, render_template, url_for

app = Flask(__name__)

@app.route('/') # index root
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit_data():
    try:
        if request.method == 'POST':
            data = request.form['data']
            return f'Submitted data: {data}'
        else:
            return 'Invalid request method'
    except Exception as e:
        return f'An error occurred: {str(e)}'

if __name__ == "__main__":
    app.run(debug=True) # this should be False in a prod environment
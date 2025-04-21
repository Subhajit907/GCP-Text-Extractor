from flask import Flask, request, render_template, send_file, redirect, url_for
from bs4 import BeautifulSoup
import io
import os
import requests
import base64
import json
import re

app = Flask(__name__)

# Function to extract text from image
def extract_text_from_image(api_key, image_file):
    base64_image = base64.b64encode(image_file.read()).decode('utf-8')
    payload = {
        "requests": [
            {
                "image": {
                    "content": base64_image
                },
                "features": [
                    {
                        "type": "TEXT_DETECTION"
                    }
                ]
            }
        ]
    }
    url = f'https://vision.googleapis.com/v1/images:annotate?key={api_key}'
    response = requests.post(url, headers={'Content-Type': 'application/json'}, data=json.dumps(payload))
    response_json = response.json()
    try:
        text_annotations = response_json.get('responses', [])[0].get('textAnnotations', [])
        text = text_annotations[0].get('description', '')
    except (IndexError, KeyError):
        text = ''
    return text

# Function to format extracted text
def format_extracted_text(text):
    formatted_text = re.sub(r'\n+', '\n', text)
    formatted_text = re.sub(r'\\u[0-9a-fA-F]{4}', '', formatted_text)
    formatted_text = re.sub(r'\s{2,}', ' ', formatted_text)
    formatted_text = re.sub(r'(Buyer.*|Bill to.*)', r'\n\1\n', formatted_text)
    formatted_text = re.sub(r'(Consignee.*|Ship to.*)', r'\n\1\n', formatted_text)
    formatted_text = re.sub(r'(Invoice No.*|Invoice Date.*)', r'\n\1\n', formatted_text)
    formatted_text = re.sub(r'(Total.*|Amount.*|GSTIN.*)', r'\n\1\n', formatted_text)
    formatted_text = re.sub(r'(Description of Goods.*|Contact.*|Transport.*)', r'\n\1\n', formatted_text)
    formatted_text = formatted_text.strip()
    return formatted_text

# Route for home page
@app.route('/', methods=['GET', 'POST'])
def index():
    extracted_text = None

    if request.method == 'POST':
        file = request.files.get('image')
        if file:
            print("Entered")
            text = extract_text_from_image('AIzaSyDzGSBIG3dX6oyKVgsUmAzH0s597EWPAQg', file)
            formatted_text = format_extracted_text(text)
            extracted_text = formatted_text 
            #print(formatted_text)
    return render_template('index.html', text=extracted_text)


# Route for downloading file
@app.route('/download')
def download_file():
    text = request.args.get('text', '')
    text_file = io.BytesIO(text.encode('utf-8'))
    text_file.seek(0)
    
    return send_file(text_file, as_attachment=True, download_name='extracted_text.txt', mimetype='text/plain')

if __name__ == '__main__':
    app.run(debug=True)

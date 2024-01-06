from flask import Flask, request, render_template, jsonify
import os

import base64
import requests
import json

import psycopg2

#need to remove this
conn=psycopg2.connect("postgresql://postgres:b633A6ag-ACAb64652fd6EBgB42-C-5F@viaduct.proxy.rlwy.net:13096/railway")
cursor = conn.cursor()

# OpenAI API Key
api_key = os.getenv('OPENAI_API_KEY')
print(api_key)

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No selected file'})

    # Get the filename
    filename = file.filename

    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    result=process_photo(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    return jsonify({'result': result})



def process_photo(filename):
    # Path to your image
    image_path = filename

    # Getting the base64 string
    base64_image = encode_image(image_path)

    headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
    }

    prompt="Please determine what object is in the picture. " \
        "Respond in a JSON format. Do not inlude '```json' in your response. " \
        "Respond with a JSON object with a top-level property called 'isTombstone' with a boolean value indicating if it is. " \
        "If it is a tombstone also include a top-level property called 'description' with a detailed description of the tombstone. " \
        "Please note it's color, shape, appearance and other chacteristics, but make no mention of the text on it. Also respond with an array containing an object for each person's lastname, firstname, middlename (if it exists), birthdate, and deathdate. " \
        "If it is not a tombstone, include a property with a detailed description of what it is. "

    payload = {
    "model": "gpt-4-vision-preview",
    "messages": [
        {
        "role": "user",
        "content": [
            {
            "type": "text",
            "text": prompt
            },
            {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{base64_image}"
            }
            }
        ]
        }
    ],
    "max_tokens": 1000,
    "temperature": 0
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

    data=response.json()['choices'][0]['message']['content']

    print(data)

    return data

'''
    parsed_json = json.loads(data)
    person_list = []

    for item in parsed_json:
        person_details = {"lastname":None, "firstname":None, "middlename":None, "birthdate":None, "deathdate":None}
        person_details['lastname'] = item['lastname']
        person_details['firstname'] = item['firstname']
        person_details['middlename'] = item['middlename']
        person_details['birthdate'] = item['birthdate']
        person_details['deathdate'] = item['deathdate']
        person_list.append(person_details)

    print(len(person_list))

    results=[]

    for person in person_list:
        sql="SELECT * FROM interments WHERE lastname = '{0}' AND firstname = '{1}'".format(person['lastname'], person['firstname'])
        print(sql)

        mycursor.execute(sql)
        result = mycursor.fetchall()

        results.append(result)

        print(result)

        return jsonify({'result': result})
'''
# Function to encode the image
def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')




if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True, port=os.getenv("PORT", default=5000))

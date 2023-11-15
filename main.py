#!/usr/bin/env python3

import json
import numpy as np
from flask import Flask, jsonify, request
from text_extraction import pdf_file_to_text, pdf_url_to_text
from information_extraction import get_output_dict
import os

app = Flask(__name__)
app.debug = True

class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NpEncoder, self).default(obj)

@app.route("/")
def home_page():
    return jsonify({
        "Availables endpoints": [{
            "POST /parse-resume?file=<your-file-name>.pdf": {
                "Intruction": "Put your file in 'data' folder in project directory, then rebuild image and run locally",
                "arguments": {
                    "file": "your-file-name.pdf"
                }
            },
            "POST /parse-resume?url=<your-web-url-to-pdf-file>": {
                "arguments": {
                    "url": "https://your-url-resume.pdf"
                }
            }
            }]
    })

@app.route("/parse-resume", methods=["POST"])
def parse_resume():

    file = request.args.get('file')
    url = request.args.get('url')

    if (file is None) and (url is None):
        return jsonify({"status": 400, "message": "You need specify either 'file' or 'url' as an argument. \
            For example: '.../parse-resume?file=sample_resume.pdf' or '.../parse-resume?url=https://my-resume.pdf'"}), 400
    elif file and url:
        return jsonify({"status": 422, "message": f"Please choose between file or URL"}), 422
    
    elif url is not None:
        text = pdf_url_to_text(url)

        output = get_output_dict(text)
        serializable_output = json.dumps(output, cls=NpEncoder)
        output_dict = json.loads(serializable_output)

        return jsonify(output_dict), 200

    elif file is not None:
        if file in os.listdir('data'):
            text = pdf_file_to_text(file)

            output = get_output_dict(text)
            serializable_output = json.dumps(output, cls=NpEncoder)
            output_dict = json.loads(serializable_output)

            return jsonify(output_dict), 200
        else:
            return jsonify({
                "status": 422, 
                "message": f"The file name {file} is not valid. You need to put your resume file in the folder 'data' and rebuild image."
                }), 422
    else:
        return jsonify({"status": 400, "message": "something went wrong"}), 400        

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
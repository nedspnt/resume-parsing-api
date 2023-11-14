#!/usr/bin/env python3

import json
import numpy as np
from flask import Flask, jsonify, request
from text_extraction import pdf_to_text
from information_extraction import get_output_dict

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
    return jsonify({"Availables endpoints": [{
        "POST": "/parse-resume?file_url=<your-file>"
    }]})

@app.route("/parse-resume", methods=["POST"])
def parse_resume():

    # receive URL of pdf file
    url = request.args.get('file_url')
    
    # pdf to text
    txt = pdf_to_text(url)

    # extract information from text
    output = get_output_dict(txt)
    serializable_output = json.dumps(output, cls=NpEncoder)
    output_dict = json.loads(serializable_output)

    return jsonify(output_dict), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
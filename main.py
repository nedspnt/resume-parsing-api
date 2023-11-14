from flask import Flask, jsonify
import json
import numpy as np
from text_extraction import pdf_to_text #, text_to_sequence
#from sentence_classification import classify_sequence
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
    return jsonify({"msg": "Use endpoint 'parse-resume'"})

@app.route("/parse-resume")
def parse_resume():
    txt = pdf_to_text()

    # full text search
    output = get_output_dict(txt)
    serializable_output = json.dumps(output, cls=NpEncoder)
    output_dict = json.loads(serializable_output)

    # sequences = text_to_sequence(txt)
    # predictions = []
    # for seq in sequences[:5]:
    #     # extract 

    #     # classify
    #     pred = classify_sequence(seq)
    #     predictions.append(
    #         {
    #             'seq': pred['sequence'], 
    #             'pred': pred['labels'][0], 
    #             'score': pred['scores'][0],
    #             'entities': get_entities_dict(seq)
    #         }
    #     )
    return jsonify(output_dict)

if __name__ == "__main__":
    # remove debug=True in production
    app.run(host="0.0.0.0", port=5001, debug=True)
import json
from transformers import pipeline

classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

output_structure = json.load(open('output_structure.json', 'r'))
candidate_labels = list(output_structure.keys())

def classify_sequence(sequence_to_classify, candidate_labels=candidate_labels):
    """ 
    Return:
        {'sequence': '...', 'label': ['skill', 'contact', ...], 'score': [0.92, 0.11, ...]}
    """
    output_dict = classifier(sequence_to_classify, candidate_labels)
    print(output_dict['labels'][0], sequence_to_classify[:10])
    return output_dict


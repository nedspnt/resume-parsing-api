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

def group_sequence():

    return None

# sequence_to_classify = """Personal Projects
# Retirement Planning App Money saving and investment planning on web app deployed on Google Cloud Run (serverless) Policy Blind Test for Thai Election 2023 Collected and labeled 400+ political policies and built a blind test web app deployed on Kubernetes.
# """
# candidate_labels = ['contact', 'education','work experience', 'project']
# print(classifier(sequence_to_classify, candidate_labels))

# qa_model = pipeline("question-answering")
# txt = """ 
# '\nNed_Jamta_CV_202305'
# ----
# '\nNED JAMTA\nE-mail: nedspnt@gmail.com Tel: +66 90 126 0689'
# ----
# 'WORK EXPERIENCE'
# ----
# '2021May Squad Lead & Data Scientist, IBM\n– Present'
# ----
# 'Responsible for pre-sale client engagements of Data & AI product portfolio, working with clients to co-create customized product\ndemo, and minimum viable solutions for business using Design Thinking methodology'"
# """
# question = "What is the most recent company this candidate is working for?"
# context = txt

# print(qa_model(question, context))


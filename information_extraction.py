import spacy
import re
from transformers import pipeline
from spacy.matcher import PhraseMatcher
from skillNer.general_params import SKILL_DB
from skillNer.skill_extractor_class import SkillExtractor
import pickle

nlp = spacy.load("en_core_web_lg")

def extract_skills(text, tresh=0.95):
    
    skill_extractor = SkillExtractor(nlp, SKILL_DB, PhraseMatcher)
    annotations = skill_extractor.annotate(text, tresh=tresh)

    skill_list = [s['doc_node_value'] for s in annotations['results']['full_matches']]
    unique_skill_list = list(set(skill_list))

    return unique_skill_list

def extract_email(text):
    """
    return:
        emails (list): [{"value"}: "xxx@gmail.com"]
    """
    emails = []
    doc = nlp(text)
    for token in doc:
        if token.like_email:
            emails.append({"value": token.text})

    return emails

def extract_phone_numbers(text):
    """
    return:
        phone_numbers (list): [{"type": "Telephone", "value": "0991234567"}]
    """

    phone_number_pattern = re.compile(r'''
        \b              # Match word boundary
        (?:             # Start of non-capturing group for optional country code
            \+?         # Optional plus sign
            \d{1,2}     # One or two digits for the country code
            \s?         # Optional whitespace character
        )?              # End of non-capturing group, entire group is optional
        \(?             # Optional opening parenthesis
        \d{2,3}         # Two or three digits for the area code
        \)?             # Optional closing parenthesis
        [-.\s]?         # Optional separator character (hyphen, period, space)
        \d{3}           # Three digits
        [-.\s]?         # Optional separator character
        \d{4}           # Four digits
        \b              # Match word boundary
    ''', re.VERBOSE)
    phone_numbers = phone_number_pattern.findall(text)

    phone_numbers_list_of_dict = [{"type": "Telephone", "value": num.replace(" ", "")} for num in phone_numbers]
    
    return phone_numbers_list_of_dict

def extract_education(text):
    
    education = []

    university_pattern = re.compile(r'''
        \s[^0-9\s]*\sUniversity\s       # <...> University
        |                               # OR
        \sUniversity\sof\s[^0-9\s]*\s   # University of <...>
    ''', re.IGNORECASE | re.DOTALL | re.MULTILINE | re.VERBOSE)

    university_matches = university_pattern.findall(text)

    unique_universities = set([u.replace('\n', ' ').strip() for u in university_matches])

    for university in unique_universities:
        education.append({
            "city": "",
            "school": university,
            "degree_name": ""
            })

    return education

def extract_experience(text):
    """
    return a list of entities
    """
    
    with open("data/companies.txt", "r") as file:
        company_master = file.read()

    entities = []
    ner_categories = ["ORG"]

    doc = nlp(text)
    for ent in doc.ents:
        txt = ent.text
        label = ent.label_
        if (label in ner_categories) and (txt.lower() in company_master.lower()):
            entities.append({txt: label})

    # # Q&A
    # with open('models/qa_model.pickle', 'rb') as file:
    #     qa_model = pickle.load(file)

    # list_of_companies_question = "What are the list of companies that a candidate have worked for since graduation?"
    # answer = qa_model(list_of_companies_question, text)

    # return answer
    
    return entities

    

def get_output_dict(text):

    output = dict()

    # skill
    output['skills'] = extract_skills(text)

    # contact
    n_alphabets = 100
    first_section = text[:n_alphabets]
    output['contact'] = dict()
    output['contact']['email'] = extract_email(first_section)
    output['contact']['phone'] = extract_phone_numbers(first_section)
    output['contact']['address'] = ""
    output['contact']['website'] = ""

    # summary
    # metadata
    # personal

    # # education
    # output['education'] = extract_education(text)

    # experience

    output['experience'] = extract_experience(text[:100])

    # ner_categories = ["ORG", "PERSON"]

    # for ent in doc.ents:
    #     if ent.label_ in ner_categories:
    #         output[ent.text] = ent.label_
    
    return output
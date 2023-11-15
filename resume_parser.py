import spacy
import re
from transformers import pipeline
from spacy.matcher import PhraseMatcher
# from skillNer.general_params import SKILL_DB
# from skillNer.skill_extractor_class import SkillExtractor
import pickle
import json

with open('models/nlp.pickle', 'rb') as file:
    nlp = pickle.load(file)

def detect_sections(text):

    text = text.lower()
    idx_location = dict()

    if "experience" in text:
        idx_location['experience'] = len(text.split('experience')[0])
    
    if "skill" in text:
        idx_location['skill'] = len(text.split('skill')[0])
    
    if "education" in text:
        idx_location['education'] = len(text.split('education')[0])

    if "certification" in text:
        idx_location['certification'] = len(text.split('certification')[0])

    if len(idx_location) > 1:
        sorted_locations = dict(sorted(idx_location.items(), key=lambda x:x[1]))
    else:
        sorted_lcoations = idx_location

    return sorted_locations

def extract_skills(text):
    """ given a text in skill section, create a list of skills"""

    skills = text.replace('\n', ' ').replace('skill', '').split(',')

    return skills

# def extract_skills_comprehensive(text, tresh=0.95):
    
#     skill_extractor = SkillExtractor(nlp, SKILL_DB, PhraseMatcher)
#     annotations = skill_extractor.annotate(text, tresh=tresh)

#     skill_list = [s['doc_node_value'] for s in annotations['results']['full_matches']]
#     unique_skill_list = list(set(skill_list))

#     return unique_skill_list

def extract_full_name(text):

    entities = []
    ner_categories = ["PERSON"]

    doc = nlp(text)
    for ent in doc.ents:
        txt = ent.text
        label = ent.label_
        if label in ner_categories:
            entities.append({txt: label})
    
    if len(entities) > 0:
        full_name = list(entities[0].keys())[0]
    else:
        full_name = ""

    return full_name

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
        education_element = {
            "city": "",
            "school": university,
            "country": "",
            "end_date": "",
            "start_date": "-",
            "degree_name": "",
            "description": "",
            "country_code": "",
            "degree_major": "",
            "custom_sections": []
        }
        education.append(education_element)

    return education

def extract_experience(text):
    """
    return a list of entities
    """
    
    with open("data/companies.txt", "r") as file:
        company_master = file.read()
    
    with open("data/job-titles.txt", "r") as file:
        job_title_master = file.read()

    experience = []
    companies = []
    ner_categories = ["DATE"]

    doc = nlp(text)

    experience_elements = dict()
    previous_entity_is_date = False
    previous_ent = ""
    for ent in doc.ents:
        if ent.label_ == "DATE":
            experience_elements[ent.text] = {
                "city": "",
                "title": "",
                "country": "",
                "employer": "",
                "end_date": "",
                "start_date": "",
                "description": "",
                "country_code": "",
                "custom_sections": []
            }
            if previous_entity_is_date:
                experience_elements[previous_ent]["end_date"] = ent.text
            else:
                experience_elements[ent.text]["start_date"] = ent.text
                previous_entity_is_date = True
            previous_ent = ent.text
        else:
            previous_entity_is_date = False

    dates = [date for date in experience_elements]
    experience_section_texts = re.split("|".join(dates), text)

    for i in range(len(experience_elements)):

        # description
        experience_elements[dates[i]]["description"] = experience_section_texts[i]

        # company
        doc = nlp(experience_section_texts[i])
        for ent in doc.ents:
            if ent.label_ == "ORG":
                experience_elements[dates[i]]["employer"] = ent.text
        
        # title TODO

        experience.append(experience_elements[dates[i]])
    
    return experience


def get_output_dict(text):

    with open('data/output_structure.json', 'r') as file:
        output = json.load(file)

    sorted_locations = detect_sections(text)
    section_names = [loc for loc in sorted_locations]
    text_sections = dict()
    # section
    if len(section_names) == 0:
        pass
    else:
        text_sections['contact'] = text.split(section_names[0])[0]
        for section_name in section_names:
            if section_name != section_names[-1]:
                next_section = section_names[section_names.index(section_name) + 1]
                text_sections[section_name] = text[sorted_locations[section_name]:sorted_locations[next_section]]
            else:
                text_sections[section_name] = text[sorted_locations[section_name]:]

    n_alphabets = 100

    # contact
    output['contact']['email'] = extract_email(text_sections['contact'])
    output['contact']['phone'] = extract_phone_numbers(text_sections['contact'])

    # skill
    if "skill" in section_names:
        output['skills'] = extract_skills(text_sections["skill"])
    else:
        output['skills'] = extract_skills(text)

    # summary
    
    # metadata

    # personal
    full_name = extract_full_name(text_sections['contact']).strip()
    output['personal']['full_name'] = full_name
    if (" " in full_name) and (len(full_name) > 3):
        output['personal']['first_name'] = full_name.split(' ')[0]
        output['personal']['family_name'] = full_name.strip().split(' ')[1]

    # education
    if "education" in section_names:
        output['education'] = extract_education(text_sections['education'])
    else:
        output['education'] = extract_education(text)

    # experience
    if "experience" in section_names:
        output['experience'] = extract_experience(text_sections['experience'])
    else:
        output['experience'] = extract_experience(text)
    
    return output
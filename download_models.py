import pickle
import spacy
from transformers import pipeline

models = dict()
models['nlp']= spacy.load('en_core_web_lg')
# models['qa_model'] = pipeline("question-answering", model="deepset/roberta-base-squad2")

for model_name in models.keys():
    with open(f'models/{model_name}.pickle', 'wb') as file:
        pickle.dump(models[model_name], file)

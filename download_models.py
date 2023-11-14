from transformers import pipeline
import pickle
import spacy

models = dict()
# models['qa_model'] = pipeline("question-answering")
models['nlp']= spacy.load('en_core_web_lg')
# models['token_classifier'] = pipeline(
#     "token-classification", model="xlm-roberta-large-finetuned-conll03-english", aggregation_strategy="simple"
# )

for model_name in models.keys():
    with open(f'models/{model_name}.pickle', 'wb') as file:
        pickle.dump(models[model_name], file)

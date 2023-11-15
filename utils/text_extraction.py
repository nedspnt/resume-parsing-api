import requests
from pdfminer.high_level import extract_text

import PyPDF2
import io

def pdf_url_to_text(url):

    res = requests.get(url)
    if res.status_code == 200:
        f = io.BytesIO(res.content)
        reader = PyPDF2.PdfReader(f)
        pages = reader.pages
        text = "".join([page.extract_text() for page in pages])

        return text
    else:
        return None

# def url_to_pdf(url):

#     res = requests.get(url)
#     if res.status_code == 200:
#         with open('data/input.pdf', 'wb') as file:
#             file.write(res.content)

#     return None

def pdf_file_to_text(file_name):

    path_to_file = f'data/{file_name}'

    return extract_text(path_to_file)

def text_to_sequence(txt):

    sentences = [s for s in txt.split('\n\n')]
    n = 3
    temp = '{} ' * n
    sequence = [temp.format(*e) for e in zip(*[iter(sentences)] * n)]
    return sequence

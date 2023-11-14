import re
from pdfminer.high_level import extract_text

def pdf_to_text(path_to_file):

    # purposefully hardcoded for this experiment
    path_to_file='data/Ned_Jamta_CV_202305.pdf'

    return extract_text(path_to_file)

def text_to_sequence(txt):

    sentences = [s for s in txt.split('\n\n')]
    n = 3
    temp = '{} ' * n
    sequence = [temp.format(*e) for e in zip(*[iter(sentences)] * n)]
    return sequence

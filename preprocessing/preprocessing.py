# -*- coding: utf-8 -*-

import pandas as pd
import nltk
import re
from nltk.corpus import stopwords
import unicodedata
from flask import Flask
app = Flask(__name__)
nltk.download('stopwords')
stopwords_list=stopwords.words('english')

def unicode_to_ascii(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
 
def clean_data(w):
    w = unicode_to_ascii(w)
    w=w.lower()                        # Lower casing
    w=re.sub(' +', ' ', w).strip(' ')  # Remove multiple whitespaces, also leading and trailing whitespaces
    w=re.sub(r'[^\w\s]','',w)          # Remove special characters and punctuation
    w=re.sub(r"([0-9])", r" ",w)       # Remove Numerical data
    w=re.sub("(.)\\1{2,}", "\\1", w)   # Remove duplicate characters
    words = w.split()                  # Tokenization

    clean_words = [word for word in words if (word not in stopwords_list) and len(word) > 2]
    return " ".join(clean_words)

@app.route('/preprocess', methods=['GET'])
def preprocess():
    opinions = pd.read_csv("./data/deceptive-opinion.csv")
    opinions['text'] = opinions['text'].apply(clean_data)
    return opinions.to_json()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001)
from nltk.util import ngrams
import pandas as pd
from flask import Flask, request, json
app = Flask(__name__)

ngramDF = pd.DataFrame([])


def ngramconvert(cleanedData,n):
    df = pd.DataFrame(cleanedData)
    df['complete_text']=df['source'] + ' ' +df['text']
    df['ngram'] = df['complete_text'].apply(lambda sentence: list(ngrams(sentence.split(), n)))
    return df


@app.route('/ngram', methods=['POST'])
def createNGram():
    jsonData = json.loads(request.data)
    if (request.args.get("ngram")):
        ngram = int(request.args.get("ngram"))
    else:
        ngram = 2
    global ngramDF 
    ngramDF = ngramconvert(jsonData,ngram)
    return "200 OK"


@app.route('/ngram', methods=['GET'])
def getGram():
    return ngramDF.to_json()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=6001)
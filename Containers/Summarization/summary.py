from flask import Flask, request, json
import pandas as pd
import pickle
import requests
import sys


app = Flask(__name__)


def summarize(opinions):
    df_truth = opinions[(opinions.deceptive == "truthful")]
    df_false = opinions[(opinions.deceptive == "deceptive")]
    true_words = df_truth['text']
    false_words = df_false['text']

    t_words = []
    f_words = []
    for word in true_words:
        t_words += word.split()
    
    for word in false_words:
        f_words += word.split()
    
    return [t_words, f_words]

    

@app.route('/datasink', methods=['POST'])
def countFreq():
    jsonData = json.loads(request.json["DATA"])
    global ngramDF 
    ngramDF = pd.DataFrame(jsonData)
    mat = summarize(ngramDF) 
    with open('summary.pickle', 'wb') as f:
        pickle.dump(mat, f)
    data = pickle.dumps(mat)
    dictionary = {}
    dictionary["DATA"] = str(data)
    dictionary["WFID"] = request.json["WFID"]
    dictionary["PORT"] = sys.argv[1]
    address = sys.argv[2]
    requests.post(address, json=dictionary)
    print("container summary complete")
    
    return "200 OK"



if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
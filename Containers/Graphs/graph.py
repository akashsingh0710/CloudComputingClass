from flask import Flask, request
import pickle
import requests
import ast
from nltk.probability import FreqDist

app = Flask(__name__)

def graph(data):
    true_words, false_words = data[0], data[1]
    mostCommonTrue = FreqDist(true_words).most_common(100)
    mostCommonFalse = FreqDist(false_words).most_common(100)
    return mostCommonTrue, mostCommonFalse
 
    

@app.route('/datasink', methods=['POST'])
def createVec():
    data = pickle.loads(ast.literal_eval(request.json["DATA"]))
    global trainingData
    trainingData = data
    fig1, fig2 = graph(trainingData)
    dictionary = {}
    dictionary["WFID"] = request.json["WFID"]
    dictionary["DATA"] = [fig1, fig2]
    address = "http://10.176.67.247:9090/output"
    # address = "http://localhost:9090/cloud"
    requests.post(address, json=dictionary)

    print("complete word cloud request")
    return "200 OK"



if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
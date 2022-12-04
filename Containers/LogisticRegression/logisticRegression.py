from flask import Flask, request
import pickle
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
import requests
import sys
import ast
import logging

app = Flask(__name__)
trainingData = []


def lr(data):
    x_train,x_test,y_train,y_test = data[0], data[1], data[2], data[3]
    lr=LogisticRegression(max_iter=100000)
    lr.fit(x_train,y_train)
    pred = lr.predict(x_test)
    score=accuracy_score(y_test,pred)
    print(score)
    return [lr, data[4], data[5]]
    


@app.route('/datasink', methods=['POST'])
def createLRModel():
    logging.basicConfig(level=logging.DEBUG)
    data = pickle.loads(ast.literal_eval(request.json["DATA"]))
    global trainingData
    trainingData = data
    model = lr(trainingData)
    data = pickle.dumps(model)
    with open('lr.pickle', 'wb') as f:
        pickle.dump(model, f)
    dictionary = {}
    dictionary["DATA"] = str(data)
    dictionary["WFID"] = request.json["WFID"]
    dictionary["PORT"] = sys.argv[1]
    address = sys.argv[2]
    requests.post(address, json=dictionary)
    logging.debug("container logistic regression complete")
    return "200 OK"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
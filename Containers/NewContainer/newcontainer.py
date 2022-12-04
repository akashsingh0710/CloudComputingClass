from flask import Flask, request, json
import logging
import requests

app = Flask(__name__)


@app.route('/datasink', methods=['POST'])
def createVec():
    logging.basicConfig(level=logging.DEBUG)
    dictionary = {}
    dictionary["DATA"] = "Hello Group 9!"
    dictionary["WFID"] = request.json["WFID"]
    address = "http://10.176.67.247:9090/hello"
    requests.post(address, json=dictionary)

    return "200 OK"


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
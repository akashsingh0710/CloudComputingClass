# -*- coding: utf-8 -*-
"""
Created on Mon Nov 21 14:12:05 2022

@author: Akash MSI
"""

from flask import Flask, render_template, request, json,redirect, url_for, jsonify
app = Flask(__name__)


workflowId = ""
res = ""

@app.route('/output', methods=['POST'])
def create():
    global workflowId 
    global res
    workflowId = request.json["WFID"]
    res = request.json["DATA"]
    return redirect(url_for('index'))


@app.route('/index/', methods=['GET'])
def index():
    # if request.args:
    #     workflowId = request.args.get("wfid")
    #     res = request.args.get("content")
    #     return render_template("index.html",  flow=workflowId, con=res)
    # return render_template("index.html")
    return render_template("index.html",  flow=workflowId, cons=res)

@app.route('/data', methods=['GET'])
def data():
    return jsonify(flow=workflowId, cons=res)


if __name__ == "__main__":
    app.run(host='http://10.176.67.247', port=9090)
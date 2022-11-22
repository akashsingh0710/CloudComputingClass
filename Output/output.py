from flask import Flask, render_template, request, json,redirect, url_for, jsonify
app = Flask(__name__)

testData = []
workflowId = ""
res = ""

@app.route('/output', methods=['POST'])
def create():
    global workflowId 
    global res
    global testData
    workflowId = request.json["WFID"]
    res = request.json["DATA"]
    testData.append((workflowId, res))
    return redirect(url_for('index'))


@app.route('/index/', methods=['GET'])
def index():
    return render_template("index.html",  testData=testData)



if __name__ == "__main__":
    app.run(host='10.176.67.247', port=9090)
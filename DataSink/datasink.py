import matplotlib
matplotlib.use("TKAgg")
from matplotlib import pyplot as plt
from wordcloud import WordCloud
import base64
import requests
import logging
from io import BytesIO
from flask import Flask, render_template, request, redirect, url_for
app = Flask(__name__)

matplotlib.pyplot.switch_backend('Agg') 


testData = []
workflowId = ""
res = ""
wfid = ""
plot_url_true = ""
plot_url_false = ""
testFreq = []
net = {
    "M1": "csa-6343-93.utdallas.edu",
	"M2": "csa-6343-103.utdallas.edu",
	"M3": "10.176.67.248",
	"M4": "10.176.67.247",
	"M5": "10.176.67.246",
	"M6": "10.176.67.245"
    }


@app.route('/cloud', methods=['POST'])
def createCloud():
    global wfid 
    global testFreq
    global plot_url_true
    global plot_url_false
    wfid = request.json["WFID"]
    imgList = request.json["DATA"]

    wordcloud = WordCloud(width=1600, height=800, background_color='white').generate(str(imgList[0]))
    plt.figure(facecolor='white')
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis('off')
    plt.title('Top 100 Most Common Words Truthful reviews', fontsize=20)
    plt.tight_layout(pad=0)
    img = BytesIO()
    plt.savefig(img, format='png')
    plt.close()
    img.seek(0)
    plot_url_true = base64.b64encode(img.getvalue()).decode('utf8')


    wordcloud = WordCloud(width=1600, height=800, background_color='white').generate(str(imgList[1]))
    matplotlib.pyplot.switch_backend('Agg') 
    plt.figure(facecolor='white')
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis('off')
    plt.title('Top 100 Most Common Words Deceptive reviews', fontsize=19)
    plt.tight_layout(pad=0)
    img = BytesIO()
    plt.savefig(img, format='png')
    plt.close()
    img.seek(0)
    plot_url_false = base64.b64encode(img.getvalue()).decode('utf8')
    dictionary = {}
    dictionary["WFID"] = wfid
    port = 6060
    for key, address in net.items():
        try:
            addr = "http://{}:{}/terminate_workflow".format(address, port)
            r = requests.post(addr, json=dictionary)
            print("status_code data sink: " , r.status_code)
              #if r.status_code == 200 and r.text == '200 OK':
            if r.status_code == 200: 
                print("sent terminate workflow")
        except Exception as e:
            print("exception!!", address)

    testFreq.append((wfid, plot_url_true, plot_url_false))
    return redirect(url_for('cloud'))

@app.route('/output', methods=['POST'])
def create():
    global workflowId 
    global res
    global testData
    workflowId = request.json["WFID"]
    res = request.json["DATA"]
    testData.append((workflowId, res))
    dictionary = {}
    dictionary["WFID"] = workflowId
    port = 6060
    for key, address in net.items():
        try:
            addr = "http://{}:{}/terminate_workflow".format(address, port)
            r = requests.post(addr, json=dictionary)
            print("status_code data sink: " , r.status_code)
              #if r.status_code == 200 and r.text == '200 OK':
            if r.status_code == 200: 
                print("sent terminate workflow")
        except Exception as e:
            print("exception!!", address)

    return redirect(url_for('index'))

@app.route('/cloud', methods=['GET'])
def cloud():
    return render_template("cloud.html",  testFreq=testFreq)


@app.route('/index/', methods=['GET'])
def index():
    return render_template("index.html",  testData=testData)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=9090)
    # app.run(host='0.0.0.0', port=9090)
    
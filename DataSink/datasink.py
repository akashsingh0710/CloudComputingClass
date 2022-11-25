import matplotlib
matplotlib.use("TKAgg")
from matplotlib import pyplot as plt
from wordcloud import WordCloud
import base64
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
    return redirect(url_for('index'))

@app.route('/cloud', methods=['GET'])
def cloud():
    return render_template("cloud.html",  testFreq=testFreq)


@app.route('/index/', methods=['GET'])
def index():
    return render_template("index.html",  testData=testData)


if __name__ == "__main__":
    app.run(host='10.176.67.247', port=9090)
    # app.run(host='0.0.0.0', port=9090)
    
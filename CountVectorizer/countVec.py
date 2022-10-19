from sklearn.feature_extraction.text import CountVectorizer
from flask import Flask, request, json
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
import pickle

app = Flask(__name__)

ngramDF = pd.DataFrame([])
    

def getTrainTestData(df):
    x=df['text']
    y=df['deceptive']
    le=LabelEncoder()
    le.fit(y)
    y = le.transform(y)
    x_train,x_test,y_train,y_test=train_test_split(x,y,random_state=0,test_size=0.2)
    count_vec = CountVectorizer(ngram_range=(1,2))
    X_train = count_vec.fit_transform(x_train)
    X_test = count_vec.transform(x_test)
    return [X_train,X_test,y_train,y_test,count_vec, le]



@app.route('/countvec', methods=['POST'])
def createVec():
    jsonData = json.loads(request.data)
    global ngramDF 
    ngramDF = pd.DataFrame(jsonData)
    return "200 OK"


@app.route('/countvec', methods=['GET'])
def getTrainingData():
    mat = getTrainTestData(ngramDF) 
    data = pickle.dumps(mat)
    with open('trainingData.pickle', 'wb') as f:
        pickle.dump(mat, f)
    return data

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=6005)
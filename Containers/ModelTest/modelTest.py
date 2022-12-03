from sklearn.feature_extraction.text import CountVectorizer
from flask import Flask, request, json
from sklearn.preprocessing import LabelEncoder
import pickle
import logging
app = Flask(__name__)
import requests
import nltk
from nltk.corpus import stopwords
nltk.download('stopwords')
stopwords_list=stopwords.words('english')
import re
import sys
import ast

import unicodedata

cv = CountVectorizer()
le = LabelEncoder()
wfid = ""
hasData = []
port = ""

def unicode_to_ascii(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
 
def clean_data(w):
    w = unicode_to_ascii(w)
    w=w.lower()                        # Lower casing
    w=re.sub(' +', ' ', w).strip(' ')  # Remove multiple whitespaces, also leading and trailing whitespaces
    w=re.sub(r'[^\w\s]','',w)          # Remove special characters and punctuation
    w=re.sub(r"([0-9])", r" ",w)       # Remove Numerical data
    w=re.sub("(.)\\1{2,}", "\\1", w)   # Remove duplicate characters
    words = w.split()                  # Tokenization

    clean_words = [word for word in words if (word not in stopwords_list) and len(word) > 2]
    return " ".join(clean_words)


testData = ["I stayed for four nights while attending a conference . The hotel is in a great spot - easy walk to Michigan Ave shopping or Rush St. , but just off the busy streets . The room I had was spacious , and very well-appointed . The staff was friendly , and the fitness center , while not huge , was well-equipped and clean . I 've stayed at a number of hotels in Chicago , and this one is my favorite . Internet was n't free , but at $ 10 for 24 hours is cheaper than most business hotels , and it worked very well .",
"we love the location and proximity to everything . The staff was very friendly and courteous . They were so nice to our 2.5 year old boy . got his backpack full of goodies the moment we arrived . We got free wifi and morning drinks by signing up for select guest program . Ca n't beat that ! the only minor issue is the elevator . we have to take 2 separate elevator trips to get to our room . It got a little annoying when we were going in and out often . Otherwise , it was a great stay !",
"I wrote an email to the sales & reservation team a week ago ... ... ... i 'm still waiting for a response . All I wanted to do was book a suite for 2 nights but they failed to even reply with an offer . We have now booked another hotel who can be bothered to answer emails . Shame you missed out , coz we tip like rockerfellers ! !",
"Not a good start when the front desk is n't willing to tell their customers that they have a problem with your room ! We reserved a King Suite , and the hotel put us in a Queen Suite without telling us up front . Only after we confronted the Manager did they come clean about the switch , he offered us a free breakfast , but would not up-grade our room . The whole problem could have been avoided if they would have told us the truth and let us decide if we still were willing to stay at the Omni . We will not be retuning to this Hotel again .",
"My family and I stayed at this hotel during an extended weekend trip in July , 08 . We had ( 3 ) 1 bedroom suites . Great Location in downtown Chicago . Within walking distance to shopping and most downtown tourist attractions . The service was excellent and the hotel staff was friendly . The breakfast buffet was very good but the eating area can get crowded . I recommend going early . The rooms were quiet and clean . I highly recommend this hotel for families and for travelers staying > 2-3 days . We would stay here again . Parking is expensive , about $ 28/day . It is valet . The cheapest self parking I could find in the area was $ 24/days so we did valet parking . The valet and bell staff were very helpful and friendly . This is my 3rd experience with Homewood Suites ( 3 different cities ) . I have had a great experience each time .",
"i valeted my lexus and it was returned with a smashed side mirror . They admitted it was their fault , and now they wo n't pay the $ 500 to fix it because we ca n't prove it was not broken before ! ! ! the hotel is wonderful , the rooms are new and nice , but we will never stay here again because of this ... .Be sure to inspect your car before you leave !",
"great expectations from the hotel of THE FUGITIVE ! Wonderful lobby ! AND THAT 'S IT ! The room was old in style and furnitures , the tv was from the other century , no minibar , no wireless internet , no wireless adapter enough for the number of the room , those guys ignore that we are in the era of IPAD without cable connections . small room , small bathroom , rude service room . they have lost my credit card number and want CASH ON DELIVERY for a breakfast of 20 dollars . Robbery in the business center , 0,59 cents a MINUTE for internet connection , you have to pay to use word , or excel . NEVER AGAIN !",
"Named my price on priceline . $ 50.00 Bucks . Hotel room was great . Clean , Clean and new . Fresh crisp sheets , comfortable bed , flat screen TV , clean carpet , nice bath , etc . Short distance to food and sightseeing . I highly recommend this property . Be prepared to pay over $ 40.00 per night to park . Hey , Its a hyatt . They also charge $ 5.00 for a bottle of water that is normally a buck . For a total of $ 100.00 nightly stay in Chicago this place is it just do n't drink the bottled water . Happy Travels",
"I was attending a training conference in Chicago and opted to book my own room thru one of the online discount programs rather than stay at the rather sterile and pedestrian hotel where the conference was being held . I booked 4 nights at the Intercontinental and was pleased with the elegance and convenient location ( an easy walk to the conference ) . From the lobby to the rooms , this hotel lives up to it 's storied reputation . ( The indoor pool seems to be imported from the set of a Busby Berkeley movie ! ) And even tho ' I was there for a conference , the hotel 's location on the Mag Mile and a quick jaunt to restaurants and theaters , made for a very pleasant stay at a very affordable price ."]


def testing(testData, model, cv):

    clean_test = [clean_data(x) for x in testData]
    reviews = cv.transform(clean_test)
    pred = model.predict(reviews)
    return testData, pred


@app.route('/testdata', methods=['POST'])
def testingData():

        global testData
        testData = request.json["DATA"]
        hasData.append(True)
        return "200 OK"



@app.route('/datasink', methods=['POST'])
def createVec():
    if hasData and hasData[0] == True:
        data = pickle.loads(ast.literal_eval(request.json["DATA"]))
        global model
        global cv
        global le
        global wfid
        global port 

        model = data[0]
        cv = data[1]
        port = sys.argv[1]
        le = data[2]

        test, pred = testing([testData], model, cv)
        prediction = le.inverse_transform(pred)

        dictionary = {}
        dictionary["WFID"] = request.json["WFID"]
        dictionary["PORT"] = sys.argv[1]
        dictionary["DATA"] = dict(zip(test, prediction))
        address = sys.argv[2]
        requests.post(address, json=dictionary)

        with open('data.json', 'w') as f:
            json.dump(dictionary, f)
        
        address = "http://10.176.67.247:9090/output"
        requests.post(address, json=dictionary)
        logging.debug("send to the client!!")
        hasData[0] = False

        return "200 OK"
    else:
        return "200 NOTOK"



if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
from sklearn.feature_extraction.text import CountVectorizer
from flask import Flask, request, json
from sklearn.preprocessing import LabelEncoder
import pickle
from sklearn.svm import SVC
app = Flask(__name__)

import nltk
from nltk.corpus import stopwords
nltk.download('stopwords')
stopwords_list=stopwords.words('english')
import re

import unicodedata

model = SVC()
cv = CountVectorizer()
le = LabelEncoder()

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

def testing(testData, model, cv):

#     test = ["My stay at the Hotel Allegro Chicago was an amazing experience ! The staff were helpful and considerate , always there to tend to my needs . My suite was extremely clean , and had all the amenities that I could ask for . I almost did n't want to leave my room , because it was so nice . But in the end I did , because the hotel is situated in such a great area , that I had to go out and see some of the sites . This hotel has wonderful rooms and service , and is in a really great area . I suggest that everyone come here if they are staying in Chicago .",
# "The Affinia Chicago is a wonderful place to stay , my husband and I stayed there for a week to visit some family and had an amazing time . The rooms were very well organized and comfortable , the staff there are very friendly , and the food there is more then amazing . we are defiantly going back next year .",
# "I was recently a guest at the Sheraton Chicago Hotel and Towers and was immensely dissatisfied . I arrived to find that they had `` lost '' my reservation . They told me they were booked solid even though I had produced my copy of the reservation confirmation . After nearly an hour of arguing with the front desk clerk she finally asked for the hotel manager to step in . He was almost helpful . He searched the database and found that there was a `` cancellation '' ; however , it was not for the type of room I had reserved . I had asked for a suite as I was going to be staying in the hotel for several days . I was given a box with a bed in it . They made no apologies for losing my reservation and offered no alternate compensation . Unfortunately , I was in town for a conference and everyone in the area was completely booked . I had no choice but to accept what they had offered . I begrudgingly accepted this with the intention of contacting the corporate office and posting my review here . Do not stay in this hotel they will NOT help you with anything , even if it was their error .",
# "Grant it , this hotel seems very nice , but I was not at all pleased with my stay here . The customer service was horrible . I had to request more towels and washcloths several times before receiving them and my linen had not been replaced either . For as much as I paid to stay here , you 'd think the least you 'd get is an iron . Not ! I had to request an iron , too ! In addition to all of the failed amenities , I was mistakenly charged twice for my stay and was n't reimbursed until an entire week later . The next time I choose to visit Chicago , Swissotel will be the last place I think to stay .",
# "The Hotel Monaco claims to be a `` boutique Chicago luxury hotel , '' but it certainly was neither luxurious nor stylish . The pictures posted on the website imply that the guest is going to stay in a room with an amazing view , but that was certainly not the case for this customer ! The decor , which might be `` cutesy '' or `` charming '' to some was actually quite tacky and outdated . The bathrooms had a musty smell and did not meet the cleanliness standards of a hotel claiming to be `` one of the top 40 hotels U.S. '' Do n't be fooled by a snappy website with some selective photos -- this hotel does not live up to its billing . You will be disappointed , as was I , if you expect anything more than a run-of-the-mill experience at a merely average hotel .",
# "I just got back from the Monaco in Chicago ! I was very pleasantly surprised , as my husband booked this trip as a last minute getaway , and he usually picks bad places-haha . Anyway , the moment we got there the doormen greeted us warmly and helped get our luggage situatated . It was busy and the line was a little long , but it moved quickly . The lady at the front desk gave us a high floor when we requested one which was very good , especially since it seemed to be near full . The room was clean and spacious ( especially considering it 's a city hotel ) . We made a lot of use of the concierge , since again , it was so last minute we did n't really make any plans . He gave us some tips and also gave us a few places we should go for Chicago pizza yummy ! It was also great being near the theater district , and basically in the thick of everything so we saved on cab fare . I thought the coolest thing was they brought you a goldfish in a bowl for your room ! very trendy . My husband is not as easily impressed , but he was really excited about the free wine hour and the free drinks in the afternoon . Overall , really nice stay in a four star , or probably four and half star hotel !"]
#     test = ["I stayed for four nights while attending a conference . The hotel is in a great spot - easy walk to Michigan Ave shopping or Rush St. , but just off the busy streets . The room I had was spacious , and very well-appointed . The staff was friendly , and the fitness center , while not huge , was well-equipped and clean . I 've stayed at a number of hotels in Chicago , and this one is my favorite . Internet was n't free , but at $ 10 for 24 hours is cheaper than most business hotels , and it worked very well .",
# "we love the location and proximity to everything . The staff was very friendly and courteous . They were so nice to our 2.5 year old boy . got his backpack full of goodies the moment we arrived . We got free wifi and morning drinks by signing up for select guest program . Ca n't beat that ! the only minor issue is the elevator . we have to take 2 separate elevator trips to get to our room . It got a little annoying when we were going in and out often . Otherwise , it was a great stay !",
# "I want to issue a travel-warning to folks who might sign up for the weekend deal they offer through travelzoo from time to time : The deal says `` free breakfast '' included in the price . However , what they do n't tell you , is that the breakfast consists of a cup of coffee and a bisquit ( or two ) ! Moreover , you need to ask for these `` tickets '' at the lobby when you check in - they wo n't give them to you automatically ! We stayed there over Christmas '03 , and we , and I noticed several guests who bought the same package , had a rather unpleasant experience ! The hotel is nice though , if you do n't consider their lousy service !",
# "Just got back from three nights at the Knickerbocker . Went up to Chicago for some last minute Christmas shopping . Hotel is in a great location . North end of Michigan Ave. about half a block away . Staff was very nice and professional . Everyone we came in contact with was very helpful . Granted this is a older hotel and some of the rooms are no bigger than closets . We were booked into a standard room and when we arrived we upgraded to a deluxe room . Good size room , with nice furnishings and a comfortable bed . Bathroom was somewhat small . Housekeeping did a great job cleaning the room every day . Did not eat at the restaurant Nix , but saw several people getting orders delivered to the bar . Overheard comments saying the food was very good . Drink service at the Martini Bar can be slow . Martinis run $ 9 and up . Very good drinks and they do n't shy away from the liquor . Valet parking was $ 35 a day with in/out priviliges . Overall a great stay . Would definately stay at this hotel in the future .",
# "My family and I stayed at this hotel during an extended weekend trip in July , 08 . We had ( 3 ) 1 bedroom suites . Great Location in downtown Chicago . Within walking distance to shopping and most downtown tourist attractions . The service was excellent and the hotel staff was friendly . The breakfast buffet was very good but the eating area can get crowded . I recommend going early . The rooms were quiet and clean . I highly recommend this hotel for families and for travelers staying > 2-3 days . We would stay here again . Parking is expensive , about $ 28/day . It is valet . The cheapest self parking I could find in the area was $ 24/days so we did valet parking . The valet and bell staff were very helpful and friendly . This is my 3rd experience with Homewood Suites ( 3 different cities ) . I have had a great experience each time .",
# "i valeted my lexus and it was returned with a smashed side mirror . They admitted it was their fault , and now they wo n't pay the $ 500 to fix it because we ca n't prove it was not broken before ! ! ! the hotel is wonderful , the rooms are new and nice , but we will never stay here again because of this ... .Be sure to inspect your car before you leave !",
# "great expectations from the hotel of THE FUGITIVE ! Wonderful lobby ! AND THAT 'S IT ! The room was old in style and furnitures , the tv was from the other century , no minibar , no wireless internet , no wireless adapter enough for the number of the room , those guys ignore that we are in the era of IPAD without cable connections . small room , small bathroom , rude service room . they have lost my credit card number and want CASH ON DELIVERY for a breakfast of 20 dollars . Robbery in the business center , 0,59 cents a MINUTE for internet connection , you have to pay to use word , or excel . NEVER AGAIN !",
# "Named my price on priceline . $ 50.00 Bucks . Hotel room was great . Clean , Clean and new . Fresh crisp sheets , comfortable bed , flat screen TV , clean carpet , nice bath , etc . Short distance to food and sightseeing . I highly recommend this property . Be prepared to pay over $ 40.00 per night to park . Hey , Its a hyatt . They also charge $ 5.00 for a bottle of water that is normally a buck . For a total of $ 100.00 nightly stay in Chicago this place is it just do n't drink the bottled water . Happy Travels",
# "I never write these reviews , but felt that it was important to state that this hotel should not be the # 1 2008 travelers choice . Terrible Service , Lazy Doormen/bellmen/concierge/valet , Lack of Respect , allow dogs to bark all morning after multiple complaints , Phantom charges to room , front dest at checkout and checkin were pompus . The icing on the cake was me watching the doormen stand and watch while a father tried to open a door to push his stroller through with his infant son , and the doorman watched on doing nothing . Me and my girlfriend are young , look young in how we dress , but in all honesty make more money than most ... and we were treated like cheap poor kids . I had dinner reservations at Spaiggia and wanted to order a car to pick us up , the concierge exclaimed that , `` You know its not jeans and running shoes right Mr . Blank ? '' Assuming I was too dumb to realize that a 5 star $ 200/person restraunt wont allow tennis shoes because I am young ? Very Dissapointed . Very nice looking , comfortable beds , great room service , contemporary , younger crowd , but service was terrible ."]
    testData = [testData]
    print(testData)
    clean_test = [clean_data(x) for x in testData]
    reviews = cv.transform(clean_test)
    pred = model.predict(reviews)
    return testData, pred


@app.route('/score', methods=['POST'])
def createVec():
    data = pickle.loads(request.data)
    global model
    global cv
    global le
    model = data[0]
    cv = data[1]

    le = data[2]
    
    return "200 OK"


@app.route('/score', methods=['GET'])
def getGram():

    testData = request.form["test"]
    test, pred = testing(testData, model, cv)
    prediction = le.inverse_transform(pred)
        
    dictionary = dict(zip(test, prediction))
    return json.dumps(dictionary)

    

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8005)
import requests
from flask import Flask, request
import pandas as pd
import time
import random
import json

net = {
	#"Manager": "M1",
	#"Routing Port": 6060,
	#"WFM Port": 5000,
  #"Data Generator 1": "csa-6343-103.utdallas.edu",
	"M1": "csa-6343-93.utdallas.edu",
	"M2": "csa-6343-103.utdallas.edu",
	"M3": "10.176.67.248",
 	"M4": "10.176.67.247",
	"M5": "10.176.67.246",
	"M6": "10.176.67.245"
}

app = Flask(__name__)


@app.route('/generate_data', methods=['POST'])
def generate_data():

    print("data generator2 generating data")
    wf = request.json
    
    file_no = random.randint(1, 116)
    
    file_name = "./test_data/test_data_{}.csv".format(file_no)
    
    
    f = open(file_name)
    Testopinions = json.load(f)
    #print(Testopinions)
    #print(type(Testopinions))
    TestDict = {}
    TestDict["DATA"] = Testopinions['Data']
    TestDict["WFID"] = wf['id']

    for item in wf['components']:
        if item['image'] == 'aditichak/modeltest':
        
          ip_add = net[item['machine']]
          port = item['port']
            
          data_gen2_sv = "http://{}:{}/testdata".format(ip_add, port)
        
          print("Try to send to this address: ")
          print(data_gen2_sv)
          
          while True:
            if request.method == 'POST': 
              
              time.sleep(30)  
              
              try:
                print("TestDict is: ")
                print(TestDict)
                r = requests.post( data_gen2_sv, json=TestDict)
                print(r.json())
                print("status_code: " , r.status_code)
                #if r.status_code == 200 and r.text == '200 OK':
                if r.status_code == 200: 
                #and r.text == '200 OK':
                  print("sent data {} to {}".format(file_name , data_gen2_sv))
                  break
              except Exception as e:
                print(e)
                print("No container found to handle the data input. Will retry...")
                time.sleep(10)
        
        
    return '200 OK'

app.run(host='10.176.67.248', port=5000)

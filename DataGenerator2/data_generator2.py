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

def generate_data():

    print("data generator2 generating data")
    # wf = request.json
    
    file_no = random.randint(1, 116)
    
    file_name = "./test_data/test_data_{}.csv".format(file_no)
    
    
    f = open(file_name)
    Testopinions = json.load(f)
    #print(Testopinions)
    #print(type(Testopinions))
    TestDict = {}
    TestDict["DATA"] = Testopinions['Data']
    # TestDict["WFID"] = wf['id']

    # print("net: " , net)
    
    for key in net:
        # if item['image'] == 'aditichak/modeltest':
          # print("key: " , key)      
          ip_add = net[key] 
          port = 6060
            
          data_gen2_sv = "http://{}:{}/pass_data_gen2".format(ip_add, port)
        
          print("Try to send to this address: " , data_gen2_sv)
          # print(data_gen2_sv)
          
          # while True:
          
          try:
          # print("TestDict is: ")
          # print(TestDict)
              r = requests.post( data_gen2_sv, json=TestDict)
              # print(r.json())
              print("status_code: " , r.status_code)
              #if r.status_code == 200 and r.text == '200 OK':
              if r.status_code == 200: 
              #and r.text == '200 OK':
                print("sent data {} to {}".format(file_name , data_gen2_sv))
          except Exception as e:
               a=1
          # print(e)
          # print("")
          # time.sleep(10)
        
    return        

    
        
while True:
    generate_data()    
    time.sleep(10)
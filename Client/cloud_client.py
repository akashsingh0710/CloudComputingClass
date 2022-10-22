import requests
import json

def create_workflow():

    workflow_string = ""
    print("Please enter the workflow file address: ")
        
    workflow_filename = input().strip()

    with open(workflow_filename, 'r') as f:
        workflow = json.load(f)

    print(workflow)

     
    #r = requests.get("http://10.176.67.108:5000/workflow?param={}".format(workflow_string) )
    r = requests.post("http://10.176.67.108:5000/workflow", json=workflow)
    print(r.text)
    return


    
create_workflow()
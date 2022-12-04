import requests
import json
import sys
import threading
import time

def create_workflow(workflow_filename=None):

    if workflow_filename == None:
        print("Please enter the workflow file address: ")
        workflow_filename = input().strip()

    with open(workflow_filename, 'r') as f:
        workflow = json.load(f)

    print(workflow)
     
    #r = requests.get("http://10.176.67.108:5000/workflow?param={}".format(workflow_string) )
    r = requests.post("http://10.176.67.108:5000/workflow", json=workflow)
    print(r.text)
    return

if len(sys.argv) > 1:
    threads = []
    with open(sys.argv[1], 'r') as f:
        workflows = json.load(f)
        for w in workflows:
            #input('Enter to send next workflow>')
            t = threading.Thread(target=create_workflow, args = (w,))
            threads.append(t)
            t.start()
    for t in threads:
        t.join()
else:
    create_workflow()
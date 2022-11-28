import requests
import json

def create_workflow():

    print("Please enter the workflow file address: ")
        
    workflow_filename = input().strip()

    with open(workflow_filename, 'r') as f:
        workflow = json.load(f)

    print(workflow)

     
    #r = requests.get("http://10.176.67.108:5000/workflow?param={}".format(workflow_string) )
    r = requests.post("http://10.176.67.108:5000/workflow", json=workflow)
    print(r.text)
    return

def kill_workflow():
    print("Please enter the workflow ID:")

    wf_ID = input().strip()

    dictionary = {}
    dictionary["WFID"] = wf_ID

    print(dictionary)

    r = requests.post("http://10.176.67.108:5000/workflow", json=dictionary)

def main():
    
    while(True):
        
        print('''
        Please Select an action:
        1. Create Workflow
        2. Kill Workflow
        3. Exit
        ''')

        response = input().strip()

        if (response == "1"):
            create_workflow()
        elif (response == "2"):
            kill_workflow()
        elif (response == "3"):
            exit()
        else:
            continue
    
if __name__=="__main__":
    main()
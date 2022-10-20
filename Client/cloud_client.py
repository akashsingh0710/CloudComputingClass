import requests


def create_workflow():

    workflow_string = ""
    print("Please enter the workflow file address: ")
        
    workflow_filename = input().strip()

    with open(workflow_filename) as workflow_file:
        
        if workflow_file.closed:
            return
        
        workflow_string = workflow_file.read()

     
    #r = requests.get("http://10.176.67.108:5000/workflow?param={}".format(workflow_string) )
    r = requests.get("http://127.0.0.1:5000/workflow?param={}".format(workflow_string) )
    print(r.text)
    return


    
create_workflow()
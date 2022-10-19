from flask import Flask
from flask import request
import json
import random


#Global Values
workflows = []
capacity = {
    "10.176.67.248":0, #PVM1
    "10.176.67.247":0, #PVM2
    "10.176.67.246":0, #PVM3
    "10.176.67.245":0, #PVM4
    "10.176.67.108":1, #UVM1 //Floor is 1 with manager already installed.
    "10.176.67.111":0  #UVM2
}
ports = []


def define_deployment(workflow_string):
    workflow_dict = json.loads(workflow_string)

    #Generate the workflow ID.
    id = 0
    while(id not in workflows):
        id = random.randint(100000, 999999)
        workflow_dict["id"] = id
        workflows.append(id)

    #select ip based off of minimum capacity. Each new container increases capacity by 1.

    for service in workflow_dict["components"]:
        temp = min(capacity.values())
        
        for ip in capacity:
            if capacity[ip] == temp:
                capacity[ip] = capacity[ip] + 1
                workflow_dict["components"][service]["ip"] = ip
                break

        #Select port that is not currently opened.

        port = 0
        while(port not in ports):
            port = random.randint(5001, 6000)
            workflow_dict["components"][service]["port"] = port
            ports.append(port)
            break
    
    #Prints data structures if flask debug mode is on.
    if app.debug == True:
        print(workflows)
        print(ports)
        print(json.dumps(workflow_dict, indent=4))

    return workflow_dict

app = Flask(__name__)

@app.route('/workflow')
def workflow():
    workflow_string = request.args.get('param')

    define_deployment(workflow_string)

    return 'Server recieved messeage: [' + workflow_string + ']'

#app.run(host='10.176.67.108', port=5000)
app.run(debug=True)



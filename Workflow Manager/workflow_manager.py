from flask import Flask, request
import json
import random
import re
import requests
import threading
import time

# Globals
with open('./network_config.json', 'r') as f:
    net = json.load(f)
vm = [] # List of machines in network config
ip_table = {} # Machine:ip. Subset of net, but mutable, so use instead of net.
routing_table = {}  # (Container ID, Workflow ID):set((nextMachineID, nextContainerID)). 
                    # One container can have to multiple next-hops. Push to routers when updated.
workflows = {} # Workflow ID:Workflow JSON dict
containers = set() # Set of used container IDs
capacity = {} # Machine:int(used space) (i.e. number of deployed services)
ports = {} # Machine:set(used ports)
app = Flask(__name__)

# Override network config for testing purposes
net = {
    "Manager": "M3",
    "Routing Port": 6060,
    "WFM Port": 5000,
    "M3": "10.176.67.248",
    "M4": "10.176.67.247",
}

def main():
    global net, vm, ip_table, workflows, capacity, ports

    # Get valid machine IDs from network config
    for k in net.keys():
        if re.fullmatch('M\d+', k):
            vm.append(k)
            ip_table[k] = net[k]

    # Init capacities and ports
    for m in vm:
        ports[m] = set()
        capacity[m] = 0
        if m == net['Manager']:
            capacity[m] += 1
    
    # Init routers on each machine
    threads = []
    for i in range(len(vm)):
        x = threading.Thread(target=router_init, args=(vm[i],ip_table,))
        threads.append(x)
        x.start()
    for t in threads:
        t.join()

    return

# REST API call destination formatter
# Takes valid machine ID and optional API path
def getAddr(id, path = None):
    global net, ip_table
    if path: 
        return 'http://' + ip_table[id] + ':' + str(net['Routing Port']) + '/' + path
    return 'http://' + ip_table[id] + ':' + str(net['Routing Port'])

# Thread function to init router on a given machine
def router_init(id, ip_table):
    while True:
        r = requests.post(getAddr(id, 'control'), json={'TYPE':'INIT', 'ID':id, 
        'MANAGER':net['Manager'], 'IPTABLE':ip_table})
        if r.status_code == 200 and r.text == id:
            break
        time.sleep(10)
    print('Router on %s started.' % id)
    return

# Thread function to update routing table info for a given machine's router
def table_update(id, routing_table):
    while True:
        r = requests.post(getAddr(id, 'control'), 
        json={'TYPE':'ROUTING', 'ROUTINGTABLE':routing_table})
        if r.status_code == 200 and r.text == '200 OK':
            break
        time.sleep(10)
    print('Router on %s updated routing info.' % id)
    return

# Thread function to deploy given service on given machine
def deploy_service(id, service):
    while True:
        r = requests.post(getAddr(id, 'deploy'), json=service)
        if r.status_code == 200 and r.text == '200 OK':
            break
        time.sleep(10)
    print('Router on %s updated routing info.' % id)
    return

# Generates deployment dict for workflow
def define_deployment(workflow_dict):
    global vm, ip_table, workflows, capacity, ports, containers

    # Generate workflow ID.
    id = random.randint(100000, 999999)
    while id in workflows:
        id = random.randint(100000, 999999)
    workflow_dict["id"] = id

    # Select machine for each component. Each new container on a machine increases capacity by 1.
    for service in workflow_dict["components"]:
        # Generate service/container ID
        cid = 'C' + str(random.randint(100000,999999))
        while id in containers:
            cid = 'C' + str(random.randint(100000, 999999))
        containers.add(cid)
        service['cid'] = cid

        temp = capacity[min(capacity, key=capacity.get)]
        for machine in capacity.keys():
            if capacity[machine] == temp:
                # Select first machine with min capacity
                capacity[machine] += 1
                service["machine"] = machine

                # Select port that is not currently opened.
                port = random.randint(5001, 6000)
                # If collision occurs, increment until open port found if port space isn't full yet.
                # (Optimization for random selection when ports are densely populated)
                while port in ports[machine] and len(ports[machine]) < 1000:
                    port += 1
                    port = (port-5001)%1000 + 5001
                service["port"] = port
                ports[machine].add(port)
                break      

    # Store workflow info
    workflows[id] = workflow_dict
    
    # Print data structures if flask debug mode is on.
    if app.debug == True:
        print(workflows.keys)
        print(ports)
        print(json.dumps(workflow_dict, indent=4))

    return workflow_dict

# Deploy workflow
def deploy(workflow_dict):
    wf = define_deployment(workflow_dict)

    # Build routing table
    for i, dest in enumerate(wf['adjacency']):
        iid = wf['components'][i]['cid']
        key = (iid, wf['id'])
        if len(dest) == 0:
            continue
        for d in dest:
            if key not in routing_table:
                routing_table[key] = set()
            dobj = wf['components'][d]
            routing_table[key].add((dobj['machine'], dobj['cid']))
        
    # Distribute routing info
    threads = []
    for i in range(len(vm)):
        x = threading.Thread(target=table_update, args=(vm[i],routing_table,))
        threads.append(x)
        x.start()

    # Deploy services 
    for service in wf['components']:
        x = threading.Thread(target=deploy_service, args=(service['machine'],
        {'image':service['image'],'cid':service['cid'], 'port':service['port']}))
        threads.append(x)
        x.start()

    for t in threads:
        t.join()

    return

# Client interface
@app.route('/workflow', methods=['POST'])
def workflow():
    global init_done
    if not init_done:
        return

    if request.method == 'POST':
        deploy(request.json)
        return 'Deploying:\n' + json.dumps(request.json)
    return

if __name__ == '__main__':
    main()
    app.run(host='0.0.0.0', port=net['WFM Port'])
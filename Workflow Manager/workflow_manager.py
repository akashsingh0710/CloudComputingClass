from flask import Flask, request
import json
import random
import re
import requests
import threading
import time

# Globals
PERSISTENT_THRESHOLD = 2
DEPLOYMENT_SCHEME = 'Worst Fit' # Round Robin, Best Fit, or Worst Fit
with open('./network_config.json', 'r') as f:
    net = json.load(f)
vm = [] # List of machines in network config
ip_table = {} # Machine:ip. Subset of net, but mutable, so use instead of net.
routing_table = {}  # (Container ID, Workflow ID):set((nextMachineID, nextContainerID)). 
                    # One container can have to multiple next-hops. Push to routers when updated.
workflows = {} # Workflow ID:Workflow JSON dict
persistent_containers = {} #Keeps track of the containers marked for persistency {image:{cid:cid, machine:machine, port:port, count:0}, image:{...}}
containers = set() # Set of used container IDs
capacity = {} # Machine:int(used space) (i.e. number of deployed services)
ports = {} # Machine:set(used ports)
app = Flask(__name__)

# Override network config for testing purposes
#net = {
#	"Manager": "M1",
#	"Routing Port": 6060,
#	"WFM Port": 5000,
#	"M1": "csa-6343-93.utdallas.edu",
#	"M2": "csa-6343-103.utdallas.edu",
#}

#M1:UVM1
#M2:UVM2
#M3:PVM1
#M3:PVM2
#M3:PVM3
#M3:PVM4

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
        json={"TYPE":"ROUTING", "ROUTINGTABLE":routing_table})
        if r.status_code == 200 and r.text == '200 OK':
            break
        time.sleep(10)
    print('Router on %s updated routing info.' % id)
    return

# Thread function to deploy given service on given machine
def deploy_service(id, service):
    while True:
        r = requests.post(getAddr(id, 'deploy'), json=service)
        print("response from deploy_service:" , r)
        if r.status_code == 200 and r.text == '200 OK':
            break
        time.sleep(10)
    print('Router on %s deployed %s.' % (id, service["cid"]))
    return

# Thread function to get VM capacity from routers
# Routers return json of the form {'CPU': 60 second avg cpu idle time, 'MEM': memory available}
def get_capacity(id, return_dict):
    while True:
        r = requests.post(getAddr(id, 'control'),
        json={'TYPE':'CAPACITY'})
        if r.status_code == 200:
            return_dict[id] = r.json()
            break
        time.sleep(10)
    return

# Returns dict of form {'vmid': {'CPU','MEM'}}
def get_vm_capacities():
    return_dict = {}
    threads = []
    for m in vm:
        t = threading.Thread(target=get_capacity, args=(m, return_dict))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()
    return return_dict

# Generates deployment dict for workflow
def define_deployment(workflow_dict):
    global vm, ip_table, workflows, capacity, ports, containers

    # Generate workflow ID.
    max_wfid = 100000
    for key in workflows.keys():
       if(key> max_wfid):
           max_wfid = key
           
    id=max_wfid+1

    # Generate workflow ID.
    #id = random.randint(100000, 999999)
    #while id in workflows:
    #    id = random.randint(100000, 999999)
    workflow_dict["id"] = id
    print("Workflow id: {} ".format(id))
    
    vm_cap = {}
    #if DEPLOYMENT_SCHEME != 'Round Robin':
    vm_cap = get_vm_capacities()
    print(vm_cap)
    # Select machine for each component. Each new container on a machine increases capacity by 1.
    for service in workflow_dict["components"]:
        
        #This portion of code will check to see if the image is already deployed.
        is_persistent = False
        image_exists = False
        for x in persistent_containers:
            if (service["image"] == x):
                persistent_containers[x]["count"] += 1
                if (persistent_containers[x]["count"] >= PERSISTENT_THRESHOLD -1):
                    service["cid"] = persistent_containers[x]["cid"]
                    service["machine"] = persistent_containers[x]["machine"]
                    service["port"] = persistent_containers[x]["port"]
                    service["persist"] = True
                    is_persistent = True
                image_exists = True

        #Generate new container
        if (is_persistent == False):
            # Generate service/container ID
            cid = 'C' + str(random.randint(100000,999999))
            while id in containers:
                cid = 'C' + str(random.randint(100000, 999999))
            containers.add(cid)
            service['cid'] = cid

            MB5 = 5 * 1024 * 1024
            CPU_VAL = 0.5
            if DEPLOYMENT_SCHEME == 'Round Robin':
                temp = capacity[min(capacity, key=capacity.get)]
                for machine in vm:
                    if capacity[machine] == temp:
                    # Select first machine with min capacity
                        capacity[machine] += 1
                        service["machine"] = machine
                        break
            elif DEPLOYMENT_SCHEME == 'Best Fit':
                sorted_vms = [x for x in vm_cap.keys()]
                sorted_vms.sort(key=lambda x: vm_cap[x]['CPU'])
                print(sorted_vms)
                for machine in sorted_vms:
                    if vm_cap[machine]['CPU'] > CPU_VAL and vm_cap[machine]['MEM'] > MB5: 
                        vm_cap[machine]['CPU'] -= CPU_VAL
                        vm_cap[machine]['MEM'] -= MB5
                        service['machine'] = machine
                        break
            elif DEPLOYMENT_SCHEME == 'Worst Fit':
                sorted_vms = [x for x in vm_cap.keys()]
                sorted_vms.sort(reverse=True, key=lambda x: vm_cap[x]['CPU'])
                print(sorted_vms)
                for machine in sorted_vms:
                    if vm_cap[machine]['CPU'] > CPU_VAL  and vm_cap[machine]['MEM'] > MB5:
                        vm_cap[machine]['CPU'] -= CPU_VAL
                        vm_cap[machine]['MEM'] -= MB5
                        service['machine'] = machine
                        break

            # Select port that is not currently opened.
            port = random.randint(5001, 6000)
            # If collision occurs, increment until open port found if port space isn't full yet.
            # (Optimization for random selection when ports are densely populated)
            while port in ports[machine] and len(ports[machine]) < 1000:
                port += 1
                port = (port-5001)%1000 + 5001
            service["port"] = port
            ports[machine].add(port)  
            
            #Mark the service to not persist
            service["persist"] = False
            
            #Adds container to be persistent.
            if (image_exists == False):
                persistent_containers.update({service["image"]:{"cid":service["cid"], "machine":service["machine"], "port":service["port"], "count":0}})

    # Store workflow info    
    workflows[id] = workflow_dict
    
    print("THIS IS THE PERSISTENCE LIST")
    print(persistent_containers)
    
    # Print data structures if flask debug mode is on.
    if app.debug == True:
        print(workflows.keys)
        print(ports)
        print(json.dumps(workflow_dict, indent=4))

    return workflow_dict

# Deploy workflow
def deploy(workflow_dict):
    wf = define_deployment(workflow_dict)

    print("Wf after define_deployment: ")
    print(wf)
    
    # Build routing table
    for i, dest in enumerate(wf['adjacency']):
        iid = wf['components'][i]['cid']
        key = iid + str(wf['id'])
        if len(dest) == 0:
            continue
        for d in dest:
            if key not in routing_table:
                routing_table[key] = list()
            dobj = wf['components'][d]
            routing_table[key].append((dobj['machine'], dobj['cid']))
    print(vm)
        
    # Distribute routing info
    threads = []
    for i in range(len(vm)):
        x = threading.Thread(target=table_update, args=(vm[i],routing_table,))
        threads.append(x)
        x.start()

    # Deploy services 
    for service in wf['components']:
        print(wf)
        x = threading.Thread(target=deploy_service, args=(service['machine'],
        {'image':service['image'],'cid':service['cid'], 'port':service['port'] , 'WFID':wf['id'], 'persist':service['persist'] }))
        threads.append(x)
        x.start()

    for t in threads:
        t.join()
        
    # data_gen1_sv = "http://{}:{}/generate_data".format(net["Data Generator 1"],  net["Data Generator Port"])    
        
    # while True:
    #     r = requests.post( data_gen1_sv, json=wf)
    #     if r.status_code == 200:
    #         break
    #     time.sleep(10)
        
        
    # data_gen2_sv = "http://{}:{}/generate_data".format(net["Data Generator 2"],  net["Data Generator Port"])    
        
    # while True:
    #     r = requests.post( data_gen2_sv, json=wf)
    #     if r.status_code == 200:
    #         break
    #     time.sleep(10)    
        
            

    return

# Client interface
@app.route('/workflow', methods=['POST'])
def workflow():
    #global init_done
    #if not init_done:
    #    return

    if request.method == 'POST':
        #print(request.json)
        deploy(request.json)
        return 'Deploying:\n' + json.dumps(request.json)
    return

if __name__ == '__main__':
    main()
    app.run(host='0.0.0.0', port=net['WFM Port'])
from flask import Flask, request
import threading
import time
import requests
import subprocess
import psutil

ROUTING_PORT = 6060

app = Flask(__name__)
vmID = None # This router's VM ID. Received in INIT control message.
managerID = None # Dataflow manager's ID. Received in INIT control message.
ip_table = {} # vm:ip_string // UPDATED BY DATAFLOW MANAGER.
container_table = {} # containerID:port // UPDATED LOCALLY. ONLY STORES LOCAL CONTAINERS.
routing_table = {} # (containerID, workflow):set((nextVMID, nextContainerID)) // UPDATED BY DATAFLOW MANAGER.
cpu_idle = []

data1_recipients = [] # (containerID, WFID)
data2_recipients = []
DATA1_IMG = ['aditichak/preprocessor-nlp']
DATA2_IMG = ['aditichak/modeltest']

#active_containers = {} #(tuple of image_name, port)
#active_WFID_for_data_gen1 = []  
#active_WFID_for_data_gen2 = []  
port_opened = []

# CPU tracking thread function
def track_cpu():
    global cpu_idle
    while True:
        if len(cpu_idle) >= 60:
            cpu_idle.pop(0)
        cpu_idle.append(100 - psutil.cpu_percent(interval=5))
        time.sleep(1)

def avg_cpu_idle():
    global cpu_idle
    if len(cpu_idle) == 0:
        return 100 - psutil.cpu_percent(interval=5)
    return sum(cpu_idle)/len(cpu_idle) 

# Container Table reverse lookup
def get_container(port):
    #print("port in get_container: ", port)
    # print("port type in get_cotainer: ", type(port))
    print(container_table)
    # print(container_table)
        
    for c in container_table.keys():
        if container_table[c] == int(port):
            return c
    return None

# REST API call destination formatter
# Takes valid vm ID and optional API path
def getAddr(vm, port=ROUTING_PORT, path = None):
    global ip_table    
    if path:
        #print("The string: " , 'http://' + ip_table[vm] + ':' + str(port) + '/' + path) 
        return 'http://' + ip_table[vm] + ':' + str(port) + '/' + path

    #print("The string2: " , 'http://' + ip_table[vm] + ':' + str(port))
    return 'http://' + ip_table[vm] + ':' + str(port)

# Container deployment
# Takes a post request with a component dict (fields: image, cid, port)
@app.route('/deploy', methods=['POST'])
def deploy_container():
    global data1_recipients, data2_recipients
    global DATA1_IMG, DATA2_IMG
    global port_opened
    
    if request.method == 'POST':
        service = request.json
        
        print("service json from deploy" , service)
        
        port = service["port"]
        WFID = service["WFID"]
        container_table[service['cid']] = port
        persist = service["persist"]
        
        # b=0
        # if service['cid'] in active_containers:
        #     a,b,c = active_containers[service['cid']]
        print("ports opened list: ", port_opened)
        print("port in json: ", port)
        
        if(persist == False):
            print("Running a newer non-persistent image!!")
            command = "sudo docker run -d"+' -p '+str(port)+':'+str(8080)+' '+service['image']
            command += ' ' + str(port) + ' ' + getAddr(vmID, path='send') # argv passed to container: [container_port] [router_address]
            result = subprocess.run(command.split(), stdout=subprocess.PIPE)    
            print("container ID deployed: " , result)
            port_opened.append(port)
        else:
            if(True):
                print("active container forloop port:" , port)
                print("Reusing persistent container!!")
            else:
                print("Running a persistent container for first time!!")
                command = "sudo docker run -d"+' -p '+str(port)+':'+str(8080)+' '+service['image']
                command += ' ' + str(port) + ' ' + getAddr(vmID, path='send') # argv passed to container: [container_port] [router_address]
                result = subprocess.run(command.split(), stdout=subprocess.PIPE)    
                print("container ID deployed: " , result)
                port_opened.append(port)
                    
        image = service['image']
        if image in DATA1_IMG:
            print(service['cid'], 'receives data from datasource 1')
            data1_recipients.append((service['cid'], service['WFID']))
        if image in DATA2_IMG:
            print(service['cid'], 'receives data from datasource 2')
            data2_recipients.append((service['cid'], service['WFID']))
        
        return '200 OK'
    return

# Handle control messages from dataflow manager
@app.route('/control', methods=['POST'])
def control():
    global vmID, managerID, ip_table, container_table, routing_table

    if request.method == 'POST':
        type = request.json['TYPE']

        if type == 'INIT':
            vmID = request.json['ID']
            managerID = request.json['MANAGER']
            ip_table = request.json['IPTABLE']
            print('I am a router on %s. My manager is %s.' % (vmID, managerID))
            print('My ip_table is', str(ip_table))
            return vmID
        if type == 'ROUTING':
            routing_table = request.json['ROUTINGTABLE']
            return '200 OK'
        if type == 'CAPACITY':
            return {'CPU': avg_cpu_idle(), 'MEM': psutil.virtual_memory().available}

    return 

# Thread function to resend messages as needed
def send_message_repeat(addr, content):
    print('Sending to ', addr)
    while True:
        try:
            r = requests.post(addr, json=content)
            if r.status_code == 200 and r.text == '200 OK':
                break
        except Exception as e:
            print("Exception from send_message_repeat")
            print(e)
        time.sleep(10)
    return

# Thread function to send a message to all next-hop destinations
# Messages between routers contain origin container in 'FROM_CONTAINER' field
def send_message(container, workflow, data, foreign=False):
    global container_table, routing_table
    # Get next-hop containers
    var = container + str(workflow)
    threads = []
    
    if var in routing_table:
        next_hops = routing_table[var]
        print(container, workflow, 'next hops', next_hops)
    
         # POST to all next-hops
        
        for next_vm, next_container in next_hops:
            if next_vm != vmID and not foreign:
                # If next-hop from origin is on another vm
                x = threading.Thread(target=send_message_repeat, 
                args=(getAddr(next_vm, ROUTING_PORT, 'send'),{'FROM_CONTAINER':container,'WFID':workflow,'DATA':data}))
                threads.append(x)
                x.start()
            elif next_vm == vmID:
                # If next-hop from origin is on this vm
                # local_vm_addr = "http://127.0.0.1:{}/datasink".format(container_table[next_container])
                x = threading.Thread(target=send_message_repeat, 
                args=(getAddr(vmID, container_table[next_container], 'datasink'),{'WFID':workflow, 'DATA':data}))
                threads.append(x)
                x.start()
    
        #print("Workflow ran successfully for Workflow Id:{} !!".format(str(workflow)))    
         
    else:
        print("No Next Hop for", container, workflow)

    for t in threads:
       t.join()
        
    return

# Container data routing.
# Container POST request must be a JSON object.
# 	It must contain workflow ID (WFID) and its transmission port (PORT) keys with correct values.
# 	It should contain a data (DATA) key mapped with its output data.
@app.route('/send', methods=['POST'])
def send():
    global vmID, managerID, ip_table, container_table, routing_table
    
    if request.method == 'POST':
        
        # Only router transmissions contain FROM_CONTAINER field
        if 'FROM_CONTAINER' not in request.json.keys():
            # Handle container transmission
            # Identify container by origin port
            port = request.json['PORT']
            container = get_container(port)
            workflow = request.json['WFID'] 
            data = request.json['DATA']

            print(vmID, 'sends', request.json.keys(), 'from', port, container, workflow)
            
            # Async send message to next-hop
            threading.Thread(target=send_message, args=(container, workflow, data), daemon=True).start()
            return '200 OK'
        else: 
            # Handle router transmission
            container = request.json['FROM_CONTAINER']
            workflow = request.json['WFID'] 
            data = request.json['DATA']

            print(vmID, 'sends', request.json.keys(), 'from', container, workflow)

            # Async send message to next-hop
            threading.Thread(target=send_message, args=(container, workflow, data, True), daemon=True).start()
            return '200 OK'

    return


@app.route('/pass_data_gen1', methods=['POST'])
def pass_data_generator1():
    opinionsDict = request.json
    # print("From pass datagen, the recieved json is: " , opinionsDict)
    # opinionsDict['PORT'] = 0
    
    threads = []
    for cid, wfid in data1_recipients:
        x = threading.Thread(target=send_message_repeat, 
        args=(getAddr(vmID, container_table[cid], 'datasink'),{'WFID':wfid, 'DATA':opinionsDict}))
        threads.append(x)
        x.start()
    for t in threads:
        t.join()

    return '200 OK' 
    
@app.route('/pass_data_gen2', methods=['POST'])
def pass_data_generator2():
    testDict = request.json
    
    threads = []
    for cid, wfid in data2_recipients:
        x = threading.Thread(target=send_message_repeat, 
        args=(getAddr(vmID, container_table[cid], 'testdata'),{'WFID':wfid, 'DATA':testDict}))
        threads.append(x)
        x.start()
    for t in threads:
        t.join()            
            
    return '200 OK'

@app.route('/terminate_workflow', methods=['POST'])
def terminate_workflow():              
    # print("wifd: {} removed".format(wfid))        
            
    return '200 OK'  


# command = "sudo docker stop $(sudo docker ps -a -q)"
# subprocess.call(command.split())
# # subprocess.call(command.split(), stdout=subprocess.PIPE)
# os.system(command)
subprocess.call('sudo docker stop $(sudo docker ps -a -q)', shell=True)
subprocess.call('sudo docker rm -f $(sudo docker ps -a -q)', shell=True)


# command = "sudo docker rm -f $(sudo docker ps -a -q)"
# subprocess.call(command.split())
# subprocess.run(command.split(), stdout=subprocess.PIPE)

app.run(host='0.0.0.0', port=ROUTING_PORT)
threading.Thread(target=track_cpu, daemon=True).start()
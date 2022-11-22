from flask import Flask, request
import threading
import time
import requests
import subprocess

ROUTING_PORT = 6060

app = Flask(__name__)
vmID = None # This router's VM ID. Received in INIT control message.
managerID = None # Dataflow manager's ID. Received in INIT control message.
ip_table = {} # vm:ip_string // UPDATED BY DATAFLOW MANAGER.
container_table = {} # containerID:port // UPDATED LOCALLY. ONLY STORES LOCAL CONTAINERS.
routing_table = {} # (containerID, workflow):set((nextVMID, nextContainerID)) // UPDATED BY DATAFLOW MANAGER.

active_containers = {} #(tuple of image_name, port)
active_WFID_for_data_gen1 = []  
active_WFID_for_data_gen2 = []  

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


# Container Table reverse lookup
def get_container(port):
    print("port in get_cotainer: ", port)
    print("port type in get_cotainer: ", type(port))
    print(container_table)
    print(container_table)
        
    for c in container_table.keys():
        if container_table[c] == int(port):
            return c
    return None

# REST API call destination formatter
# Takes valid vm ID and optional API path
def getAddr(vm, port=ROUTING_PORT, path = None):

    print("port" , port)
    print("routing_port" , ROUTING_PORT)
    print("path" , path)

    global ip_table
    if path:
        print("The string: " , 'http://' + ip_table[vm] + ':' + str(port) + '/' + path) 
        return 'http://' + ip_table[vm] + ':' + str(port) + '/' + path

    print("The string2: " , 'http://' + ip_table[vm] + ':' + str(port))
    return 'http://' + ip_table[vm] + ':' + str(port)

# Container deployment
# Takes a post request with a component dict (fields: image, cid, port)
@app.route('/deploy', methods=['POST'])
def deploy_container():
    global active_WFID_for_data_gen1, active_WFID_for_data_gen2
    if request.method == 'POST':
        service = request.json
        port = service["port"]
        WFID = service["WFID"]
        container_table[service['cid']] = port
        command = "sudo docker run -d"+' -p '+str(port)+':'+str(8080)+' '+service['image']
        command += ' ' + str(port) + ' ' + getAddr(vmID, path='send') # argv passed to container: [container_port] [router_address]
        subprocess.run(command.split(), stdout=subprocess.PIPE)
        active_containers[service['cid']] = (service['image'] , service['port'])
        
        
        if WFID not in active_WFID_for_data_gen1:
            active_WFID_for_data_gen1.append(WFID)
            
        if WFID not in active_WFID_for_data_gen2:    
            active_WFID_for_data_gen2.append(WFID)
        print("active WFID for data gen1: " , active_WFID_for_data_gen1)
        print("active WFID for data gen2: " , active_WFID_for_data_gen2)
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

    return 

# Thread function to resend messages as needed
def send_message_repeat(addr, content):
    while True:
        r = requests.post(addr, json=content)
        if r.status_code == 200 and r.text == '200 OK':
            break
        time.sleep(10)
    return

# Thread function to send a message to all next-hop destinations
# Messages between routers contain origin container in 'FROM_CONTAINER' field
def send_message(container, workflow, data):
    global container_table, routing_table
    # Get next-hop containers
    next_hops = routing_table[container + str(workflow)]
    # POST to all next-hops
    threads = []
    for next_vm, next_container in next_hops:
        if next_vm != vmID:
            # If next-hop from origin is on another vm
            x = threading.Thread(target=send_message_repeat, 
            args=(getAddr(next_vm, ROUTING_PORT , 'send'),{'FROM_CONTAINER':container,'WFID':workflow,'DATA':data}))
            threads.append(x)
            x.start()
        else:
            # If next-hop from origin is on this vm
            x = threading.Thread(target=send_message_repeat, 
            args=(getAddr(next_vm, container_table[next_container], 'datasink'),{'WFID':workflow, 'DATA':data}))
            threads.append(x)
            x.start()
    for t in threads:
        t.join()
        
    #print("Workflow ran successfully for Workflow Id:{} !!".format(str(workflow)))    
        
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
            # Async send message to next-hop
            threading.Thread(target=send_message, args=(container, workflow, data), daemon=True).start()
            return '200 OK'
        else: 
            # Handle router transmission
            container = request.json['FROM_CONTAINER']
            workflow = request.json['WFID'] 
            data = request.json['DATA']
            # Async send message to next-hop
            threading.Thread(target=send_message, args=(container, workflow, data), daemon=True).start()
            return '200 OK'

    return


@app.route('/pass_data_gen1', methods=['POST'])
def pass_data_generator1():
    opinionsDict = request.json
    # print("From pass datagen, the recieved json is: " , opinionsDict)
    
    
    # print("active_WFID_for_data_gen1: " , active_WFID_for_data_gen1)
    if(len(active_WFID_for_data_gen1)>0):
        opinionsDict['WFID'] = active_WFID_for_data_gen1[0]
        
        
        print("active containers from data gen1: " , active_containers)
        for key in active_containers:
            image , port  = active_containers[key]
            if(image == 'aditichak/preprocessor-nlp'):
                print("image: " , image , " found!")
                router_addr = "http://{}:{}/datasink".format(net[vmID], port)
            
                try:
                    print("Inside TRy of DatgEn1")
                    r = requests.post(router_addr, json=opinionsDict)
                    print("Afsafa: " , r)
                    print("status_code: " , r.status_code)
                    if r.status_code == 200:
                        active_WFID_for_data_gen1.pop(0)
                        print("sent data to {}".format(router_addr))
                except Exception as e:
                     print(e)
            
    return '200 OK' 
    
    
    
@app.route('/pass_data_gen2', methods=['POST'])
def pass_data_generator2():
    TestDict = request.json
    
    # print("From pass data_gen2, the recieved json is: " , TestDict)
    
    # print("active_WFID_for_data_gen2: " , active_WFID_for_data_gen2)
    
    if(len(active_WFID_for_data_gen2)>0):
        TestDict['WFID'] = active_WFID_for_data_gen2[0]
        
        print("active containers from data gen2 please please: " , active_containers)
        print("Yahooo1")
        for key in active_containers:
            print("Yahooo2")
            print("this is the key from datagen2: ", key , "in activecontainer")
            image , port  = active_containers[key]
            print("image from data_gen2: " , image)
            if(image == 'aditichak/modeltest'):    
                print("image: " , image , " found!")
                router_addr = "http://{}:{}/testdata".format(net[vmID], port)
                print("sent to: ", router_addr)
                try:
                    r = requests.post(router_addr, json=TestDict)
                    print("status_code: " , r.status_code)
                    if r.status_code == 200 and r.text == "200 OK":
                        active_WFID_for_data_gen2.pop(0)
                        print("sent data to {}".format(router_addr))
                except Exception as e:
                     print(e)
            
        print("out of loop active containers from data gen2:")            
            
    return '200 OK'     


app.run(host='0.0.0.0', port=ROUTING_PORT)

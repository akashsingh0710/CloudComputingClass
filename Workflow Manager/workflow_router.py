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

# Container Table reverse lookup
def get_container(port):
    for c in container_table.keys:
        if container_table[c] == port:
            return c
    return None

# REST API call destination formatter
# Takes valid vm ID and optional API path
def getAddr(vm, port=ROUTING_PORT, path = None):
    global ip_table
    if path: 
        return 'http://' + ip_table[vm] + ':' + str(port) + '/' + path
    return 'http://' + ip_table[vm] + ':' + str(port)

# Container deployment
# Takes a post request with a component dict (fields: image, cid, port)
@app.route('/deploy', methods=['POST'])
def deploy_container():
    if request.method == 'POST':
        service = request.json
        port = service["port"]
        container_table[service['cid']] = port
        command = "sudo docker run -it"+' -p '+str(port)+':'+str(8080)+' '+service['image']
        command += ' ' + str(port) + ' ' + getAddr(vmID, path='send') # argv passed to container: [container_port] [router_address]
        subprocess.run(command.split(), stdout=subprocess.PIPE)
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
    next_hops = routing_table[(container, workflow)]
    # POST to all next-hops
    threads = []
    for next_vm, next_container in next_hops:
        if next_vm != vmID:
            # If next-hop from origin is on another vm
            x = threading.Thread(target=send_message_repeat, 
            args=(getAddr(next_vm, 'send'),{'FROM_CONTAINER':container,'WFID':workflow,'DATA':data}))
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

app.run(host='0.0.0.0', port=ROUTING_PORT)

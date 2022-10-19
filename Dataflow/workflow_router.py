from flask import Flask, request
import threading
import time
import requests

ROUTING_PORT = 6060

app = Flask(__name__)
vmID = None # This router's VM ID. Received in INIT control message.
managerID = None # Dataflow manager's ID. Received in INIT control message.
ip_table = {} # vm:ip_string // UPDATED BY DATAFLOW MANAGER.
container_table = {} # containerID:port // UPDATED LOCALLY. ONLY STORES LOCAL CONTAINERS.
routing_table = {} # (containerID, workflow):(nextVMID, nextContainerID) // UPDATED BY DATAFLOW MANAGER.

# Container Table reverse lookup
def get_container(port):
	for c in container_table.keys:
		if container_table[c] == port:
			return c
	return None

# REST API call destination formatter
# Takes valid machine ID and optional API path
def getAddr(vm, port=ROUTING_PORT, path = None):
	global ip_table
	if path: 
		return 'http://' + ip_table[vm] + ':' + str(port) + '/' + path
	return 'http://' + ip_table[vm] + ':' + str(port)

# Container deployment
@app.route('/container', methods=['POST'])
def deploy_container():
	# Jiazheng TODO
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

	return 

# Thread function to resend messages as needed
# Messages between routers contain origin container in 'CONTAINER' field
def send_message(container, workflow, data):
	global container_table, routing_table
	while True:
		# Get next-hop container
		next_container, next_vm = routing_table[(container, workflow)]
		# Try to POST
		if next_vm != vmID:
			# If next-hop from origin is on another vm
			r = requests.post(getAddr(next_vm, 'send'), 
			json={'FLAG':1,'CONTAINER':container,'WFID':workflow,'DATA':data})
			if r.status_code == 200 and r.text == '200 OK':
				break
		else:
			# If next-hop from origin is on this vm
			r = requests.post(getAddr(next_vm, container_table[next_container], 'datasink'), 
			json={'WFID':workflow, 'DATA':data})
			if r.status_code == 200 and r.text == '200 OK':
				break
		time.sleep(10)
	return

# Container data routing.
# Container POST request must be a JSON object.
# 	It must contain workflow ID (WFID) and its transmission port (PORT) keys with correct values.
# 	It should contain a data (DATA) key mapped with its output data.
@app.route('/send', methods=['POST'])
def send():
	global vmID, managerID, ip_table, container_table, routing_table

	if request.method == 'POST':
		# Routers set a flag that a message is a router transmission
		if 'FLAG' not in request.json.keys():
			# Handle container transmission
			# Identify container by port
			port = request.json['PORT']
			container = get_container(port)
			workflow = request.json['WFID'] 
			data = request.json['DATA']
			# Async send message to next-hop
			threading.Thread(target=send_message, args=(container, workflow, data), daemon=True).start()
			return '200 OK'
		else: 
			# Handle router transmission
			container = request.json['CONTAINER']
			workflow = request.json['WFID'] 
			data = request.json['DATA']
			# Async send message to next-hop
			threading.Thread(target=send_message, args=(container, workflow, data), daemon=True).start()
			return '200 OK'

	return

app.run(host='0.0.0.0', port=ROUTING_PORT)

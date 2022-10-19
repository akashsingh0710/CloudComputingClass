from flask import Flask, request

app = Flask(__name__)
ROUTING_PORT = 5050
vmID = None # This router's VM ID. Received in INIT control message.
managerID = None # Dataflow manager's ID. Received in INIT control message.
ip_table = {} # vm:ip_string
container_table = {} # containerID:(vm, port)
routing_table = {} # containerID:nextContainerID

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

# Container data routing
@app.route('/send', methods=['POST'])
def send():
	return

app.run(host='0.0.0.0', port=ROUTING_PORT)

import json
import re
import requests
import threading
import time

#net = json.load(open('./network_config.json', 'r'))

net = {
	"Dataflow Manager": "M3",
	"Routing Port": 6060,
	"M3": "10.176.67.248",
	"M4": "10.176.67.247",
}

# REST API call destination formatter
# Takes valid machine ID and optional API path
def getAddr(id, path = None):
	global net
	if path: 
		return 'http://' + net[id] + ':' + str(net['Routing Port']) + '/' + path
	return 'http://' + net[id] + ':' + str(net['Routing Port'])

# Thread function to init routers on each machine in the network
def router_init(id, ip_table):
	while True:
		r = requests.post(getAddr(id, 'control'), json={'TYPE':'INIT', 'ID':id, 
		'MANAGER':net['Dataflow Manager'], 'IPTABLE':ip_table})
		if r.status_code == 200 and r.text == id:
			break
		time.sleep(10)
	print('Router on %s started.' % id)
	return

def main():
	# Get valid machine IDs from network config
	vm = []
	ip_table = {}
	for k in net.keys():
		if re.fullmatch('M\d+', k):
			vm.append(k)
			ip_table[k] = net[k]
	
	# Init routers on each machine
	threads = []
	for i in range(len(vm)):
		x = threading.Thread(target=router_init, args=(vm[i],ip_table,))
		threads.append(x)
		x.start()
	for t in threads:
		t.join()
	
	return

if __name__ == '__main__':
	main()
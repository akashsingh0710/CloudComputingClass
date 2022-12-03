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

data1_recipients = [] # (containerID, WFID)
data2_recipients = []
DATA1_IMG = ['aditichak/initial-process']
DATA2_IMG = ['aditichak/modeltest']

#active_containers = {} #(tuple of image_name, port)
#active_WFID_for_data_gen1 = []  
#active_WFID_for_data_gen2 = []  
port_opened = []

# Container Table reverse lookup
def get_container(port):
    print("port in get_container: ", port)
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

    print("port" , port)
    print("routing_port" , ROUTING_PORT)
    print("path" , path)

    global ip_table
    
    print("vm: " , vm)
    
    if path:
        print("The string: " , 'http://' + ip_table[vm] + ':' + str(port) + '/' + path) 
        return 'http://' + ip_table[vm] + ':' + str(port) + '/' + path

    print("The string2: " , 'http://' + ip_table[vm] + ':' + str(port))
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
            if(port in port_opened):
                print("active container forloop port:" , port)
                print("Reusing persistent container!!")
            else:
                print("Running a persistent container for first time!!")
                command = "sudo docker run -d"+' -p '+str(port)+':'+str(8080)+' '+service['image']
                command += ' ' + str(port) + ' ' + getAddr(vmID, path='send') # argv passed to container: [container_port] [router_address]
                result = subprocess.run(command.split(), stdout=subprocess.PIPE)    
                print("container ID deployed: " , result)
                port_opened.append(port)
                    
            
        # elif(persist == True and (service['cid'] not in active_containers)):
        #     print("Running a persistent container for first time!!")
        #     command = "sudo docker run -d"+' -p '+str(port)+':'+str(8080)+' '+service['image']
        #     command += ' ' + str(port) + ' ' + getAddr(vmID, path='send') # argv passed to container: [container_port] [router_address]
        #     result = subprocess.run(command.split(), stdout=subprocess.PIPE)    
        #     print("container ID deployed: " , result)
        # else:
        #     print("Reusing persistent container!!")
        image = service['image']
        if image in DATA1_IMG:
            data1_recipients.append((service['cid'], service['WFID']))
        if image in DATA2_IMG:
            data2_recipients.append((service['cid'], service['WFID']))
        
        if(image == 'aditichak/initial-process'):
            print("start first container: image: " , str(image) , " with wfid: ", str(WFID) , " and port: ", str(port))
            # router_addr = "http://{}:{}/datasink".format(net[vmID], port)
           
            WFID_JSON = {}
            WFID_JSON['WFID'] = str(WFID)
                
            
                # print("Inside TRy of DatgEn1")
                # print("opinionsDict: /n" + opinionsDict)
            a=0    
            while a==0:
                router_addr="http://127.0.0.1:{}/datasink".format(port)
                try:
                    r=requests.post(router_addr, json=WFID_JSON)
                    # r = requests.post(router_addr, json=WFID_JSON)
                    # print("Afsafa: " , r)
                    print("status_code: " , r.status_code)
                    if r.status_code == 200 and r.text == "200 OK":
                        print("DataFlowManager sucessfully started image: {}, port: {}, wfid: {}".format(image , port, WFID))
                        # active_containers.pop(service['cid'])
                        print("sent data to {}".format(router_addr))
                        a=1
                        break
                    time.sleep(10)
                    # if r.status_code == 200 and r.text == "200 NOTOK":
                    #     print("Port and WFID mismatch")
                    #     break
                except Exception as e:
                    print("Exception from dataflowManager")
                    print("execption with address: " , router_addr)
                    print(e)        
                    time.sleep(10)
                 
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
        try:
            r = requests.post(addr, json=content)
            if r.status_code == 200 and r.text == '200 OK':
                break
            time.sleep(10)
        except Exception as e:
            time.sleep(10)
            print("Exception from send_message_repeat")
            print(e)
    return

# Thread function to send a message to all next-hop destinations
# Messages between routers contain origin container in 'FROM_CONTAINER' field
def send_message(container, workflow, data):
    global container_table, routing_table
    # Get next-hop containers
    var = container + str(workflow)
    print("var: " , var)
    threads = []
    
    print("debugging send_message")
    if var in routing_table:
        print("debugging send_message is in IF condition, var:", var , routing_table)
        next_hops = routing_table[var]
    
         # POST to all next-hops
        
        for next_vm, next_container in next_hops:
           if next_vm != vmID:
               # If next-hop from origin is on another vm
               
               print("From send message function container: {} , workflow: {}".format(container, workflow))
               
               x = threading.Thread(target=send_message_repeat, 
               args=(getAddr(next_vm, ROUTING_PORT , 'send'),{'FROM_CONTAINER':container,'WFID':workflow,'DATA':data}))
               threads.append(x)
               x.start()
           else:
               # If next-hop from origin is on this vm
               local_vm_addr = "http://127.0.0.1:{}/datasink".format(container_table[next_container])
               # x = threading.Thread(target=send_message_repeat, 
               # args=(getAddr(next_vm, container_table[next_container], 'datasink'),{'WFID':workflow, 'DATA':data}))
               x = threading.Thread(target=send_message_repeat, 
               args=(local_vm_addr,{'WFID':workflow, 'DATA':data}))
               threads.append(x)
               x.start()
    
        #print("Workflow ran successfully for Workflow Id:{} !!".format(str(workflow)))    
         
    else:
        
        print("No Next Hop available!")
        # print("debugging send_message is in ELSE condition, var:", var , routing_table)
        # for key in net:
        #     ip_add = net[key] 
        #     port = 6060
        #     WFID_to_terminate= {}
        #     WFID_to_terminate['WFID'] = str(workflow)
        #     router_addr = "http://{}:{}/terminate_workflow".format(ip_add, port)
        
        #   # print("Terminate workflow id: " + str(workflow))
                          
        #     try:
        #         r = requests.post(router_addr, json=WFID_to_terminate)
        #         print("status_code: " , r.status_code)
        #         if r.status_code == 200:
        #       # and r.text == '200 OK':
        #             print("workflow: {} terminated at {}".format(str(workflow) , router_addr))
        #     except Exception as e:
        #         # print(e)
        #         print()
        
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

    print("Send call in WFR's container_table ", container_table)
    if request.method == 'POST':
        # Only router transmissions contain FROM_CONTAINER field
        if 'FROM_CONTAINER' not in request.json.keys():
            # Handle container transmission
            # Identify container by origin port
            port = request.json['PORT']
            container = get_container(port)
            workflow = request.json['WFID'] 
            data = request.json['DATA']
            
            print("IFFFF:  port: {} , containerID: {} , workflowid: {}".format(port, container, workflow))
            # Async send message to next-hop
            threading.Thread(target=send_message, args=(container, workflow, data), daemon=True).start()
            return '200 OK'
        else: 
            # Handle router transmission
            container = request.json['FROM_CONTAINER']
            workflow = request.json['WFID'] 
            data = request.json['DATA']
            # Async send message to next-hop
            print("ELSEEEE: containerID: {} , workflowid: {}".format( container, workflow))
            threading.Thread(target=send_message, args=(container, workflow, data), daemon=True).start()
            return '200 OK'

    return


@app.route('/pass_data_gen1', methods=['POST'])
def pass_data_generator1():
    opinionsDict = request.json
    # print("From pass datagen, the recieved json is: " , opinionsDict)
    # opinionsDict['PORT'] = 0
    
    threads = []
    for cid, wfid in data1_recipients:
        local_vm_addr = "http://127.0.0.1:{}/datasink".format(container_table[cid])
        x = threading.Thread(target=send_message_repeat, 
        args=(local_vm_addr,{'WFID':wfid, 'DATA':opinionsDict}))
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
        local_vm_addr = "http://127.0.0.1:{}/datasink".format(container_table[cid])
        x = threading.Thread(target=send_message_repeat, 
        args=(local_vm_addr,{'WFID':wfid, 'DATA':testDict}))
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
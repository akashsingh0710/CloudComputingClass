import subprocess
import json
from flask import Flask
from flask import request




def deploy_container(workflow_dict):
    global vmID,ip_table
    for service in workflow_dict["components"]:
        image=workflow_dict["components"][service]["image"]
        port=workflow_dict["components"][service]["port"]
        ip=workflow_dict["components"][service]["ip"]
        network=None #the name of the network
        command_list=[]
        #create the container
        command_1="sudo docker run -it --name "+service+' -p '+port+':'+port+' '+image
        command_list.append(command_1)
        #connect the container to the network
        command_2="sudo docker network connect --ip "+ip+' '+network+' 'service
        command_list.append(command_2)
        #connnect the container to the link-local address
        command_3="sudo docker network connect --link-local-ip "+ip_table+' '+network+' 'service
        command_list.append(command_3)
        
        #run the commands
        result_list=[]
        for command in command_list:
            result=subprocess.run(command.split(), stdout=subprocess.PIPE)
            result_list.append(result)
        return result_list


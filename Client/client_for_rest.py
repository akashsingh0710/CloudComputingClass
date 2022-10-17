import requests

while True:

    i=1
    workflow_string = ""
    print("Please enter the image name for workflow component {}:".format(i))
    while True:
        
        image = input().strip()


        if(image=="done"):
            r = requests.get("http://10.176.67.108:5000/workflow?param={}".format(workflow_string) )   
            print(r.text)
            break
        

        if(image=="exit"):
            print("\nBye Bye!")
            exit(1)
        

        workflow_string = workflow_string + " " + image
        i=i+1
        print("Please enter the image name for workflow component {}:".format(i))


        


    

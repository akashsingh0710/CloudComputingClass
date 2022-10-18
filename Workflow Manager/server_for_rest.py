import requests
from flask import Flask
from flask import request

app = Flask(__name__)

@app.route('/workflow')
def index():
    workflow_string = request.args.get('param')
    return 'Server recieved messeage: [' + workflow_string + ']'

app.run(host='10.176.67.108', port=5000)




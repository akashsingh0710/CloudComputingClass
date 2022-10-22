#!/usr/bin/env python
# coding: utf-8

# In[1]:


from flask import Flask, request, jsonify


# In[2]:


RECEIVER_PORT=5050


# In[3]:


app = Flask(__name__)


# In[ ]:


@app.route("/receiver",methods=["GET","POST"])
def receiver():
    content=request.json
    print(content)
    return 'OK'
app.run(host='0.0.0.0', port=RECEIVER_PORT)


# In[ ]:





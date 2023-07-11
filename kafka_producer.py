#!/usr/bin/env python
# coding: utf-8

# In[24]:


import pandas as pd 
from kafka import KafkaConsumer, KafkaProducer
from time import sleep 
from json import dumps 
import json
import random


# In[25]:


# Define Producer
producer = KafkaProducer(bootstrap_servers=["ec2-44-206-255-156.compute-1.amazonaws.com"],
                         value_serializer = lambda x: dumps(x).encode('utf-8'))


# In[26]:


# Read Sample Data to send to Kafka Consumer
df = pd.read_csv("indexProcessed.csv")


# In[ ]:


while True: 
    # Wait for random time beween 0 ~ 10 seconds
    sleep(random.uniform(0,3)) 
    # Generate random data 
    generated_data = df.sample(1).to_dict(orient='records')[0]
    # Send it to the kafka consumer 
    producer.send("demo_test", value=generated_data)
    


# In[ ]:





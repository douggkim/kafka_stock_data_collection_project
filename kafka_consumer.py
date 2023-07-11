#!/usr/bin/env python
# coding: utf-8

# In[38]:


from kafka import KafkaConsumer
from time import sleep 
from json import dumps, loads
import json
from s3fs import S3FileSystem
from datetime import datetime
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


# In[39]:


# Declare Kafka Consumer
consumer = KafkaConsumer(
    'demo_test',
    bootstrap_servers=["ec2-44-206-255-156.compute-1.amazonaws.com:9092"],
    value_deserializer = lambda x: loads(x.decode('utf-8')))


# In[42]:


# Create S3 Object 
s3 = S3FileSystem() 

# Intialize a list to hold the data 
tmp_data = [] 

for count, message in enumerate(consumer): 
    # Append the data to the list 
    tmp_data.append(message.value)
    # If we collect 10 messages save it to a parquet file
    if count != 0 and count % 10 == 0: 
        # Create a pandas DataFrame from the accumulated data
        df = pd.DataFrame(tmp_data)

        # Convert the DataFrame to a PyArrow table
        table = pa.Table.from_pandas(df)
        
        # Record current time to use in file name 
        current_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S%Z")
        with s3.open(f"s3://kafka-stock-data-trial/stock_market_data_        {current_timestamp}.parquet", "wb") as file:
            print(table)
            pq.write_table(table, file)    
            #Renew the list 
            tmp_data = []

# If there are remaining rows that haven't been written to a file
if tmp_data:
    df = pd.DataFrame(tmp_data)
    table = pa.Table.from_pandas(df)
    current_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S%Z")
    file_name = f"stock_market_data_{current_timestamp}.parquet"
    with s3.open(f"s3://kafka-stock-data-trial/{file_name}", "wb") as file:
        pq.write_table(table, file)


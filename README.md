# Sample Project

# Resource
Great thanks to Darshil Parmar for putting together such an easy-to-follow project! 
I made adjustments to Kafka consumer and glue crawler part to fit my use cases. 

[https://www.youtube.com/watch?v=KerNf0NANMo](https://www.youtube.com/watch?v=KerNf0NANMo)

# Environment Setup

## 1. Set up EC2 Instance

EC2 Instance should have linux as OS and T2 Micro tier (free-tier) to make life easier 

## 2. Install Apache Kafka on EC2

1. Install Kafka 
    
    ```bash
    wget https://archive.apache.org/dist/kafka/3.3.1/kafka_2.13-3.3.1.tgz
    tar -xvf kafka_2.13-3.3.1.tgz
    ```
    
2. Install Java (Kafka runs on JVM) 
    
    ```bash
    sudo yum install java-1.8.0-amazon-corretto.x86_64
    ```
    
3. Start Zookeeper 
    
    ```bash
    ./kafka_2.13-3.3.1/bin/zookeeper-server-start.sh ./kafka_2.13-3.3.1/config/zookeeper.properties
    ```
    
4. Increase memory to Kafka Heap 
    
    ```bash
    export KAFKA_HEAP_OPTS="-Xmx256M -Xms128M"
    ```
    
5. Start Kafka
    
    ```bash
    cd kafka_2.12-3.3.1
    ./kafka_2.13-3.3.1/bin/kafka-server-start.sh ./kafka_2.13-3.3.1/config/server.properties 
    ```
    
6. Make the Kafka listen through public IP
    
    ```bash
    vim ./config/server.properties 
    
    # Change this part 
    # Listener name, hostname and port the broker will advertise to clients.
    # If not set, it uses the value for "listeners".
    advertised.listeners=PLAINTEXT://ec2-54-237-239-178.compute-1.amazonaws.com:9092
    ```
    
7. Rerun Zoo-Keeper and Kafka

## 3. Allow Traffic for the EC2 Instance

1. Allow Inbound traffic on AWS console (`Instance Details → Security → Inbound Rules → launch-wizard-1 → {security group name} → edit inbound rules` ) 
    
    ![Untitled](https://github.com/dougieduk/kafka_stock_data_collection_project/blob/main/resources_for_md/images/Untitled.png)
    

## 4. Create Topic

```bash
cd kafka_2.13-3.3.1
bin/kafka-topics.sh --create --topic demo_test --bootstrap-server 54.237.239.178:9092 --replication-factor 1 --partitions 1
```

## 5. Start Producer

```bash
./kafka_2.13-3.3.1/bin/kafka-console-producer.sh --topic demo_test --bootstrap-server ec2-44-206-255-156.compute-1.amazonaws.com:9092
```

## 6. Start Consumer

```bash
cd kafka_2.13-3.3.1
./kafka_2.13-3.3.1/bin/kafka-console-consumer.sh --topic demo_test --bootstrap-server ec2-44-206-255-156.compute-1.amazonaws.com:9092
```

## 7. Use Python to run Kafka Consumer/ Producer

```bash
# Define Producer
producer = KafkaProducer(bootstrap_servers=["ec2-44-206-255-156.compute-1.amazonaws.com"],
                         value_serializer = lambda x: dumps(x).encode('utf-8'))
while True: 
    # Wait for random time beween 0 ~ 10 seconds
    sleep(random.uniform(0,3)) 
    # Generate random data 
    generated_data = df.sample(1).to_dict(orient='records')[0]
    # Send it to the kafka consumer 
    producer.send("demo_test", value=generated_data)

# Flush the data in producer 
producer.flush() 

============On a seperate File============

consumer = KafkaConsumer(
    'demo_test',
    bootstrap_servers=["ec2-44-206-255-156.compute-1.amazonaws.com:9092"],
    value_deserializer = lambda x: loads(x.decode('utf-8')))

for c in consumer: 
    print(c.value)
```

# Set up AWS Storage

## 1. Create S3 Bucket

## 2. Go to IAM and Create the role with the permission

### Create User

1. user  → Add user 
2. Check `Access Key - Programmatic access` 
3. `Attach existing policies directly` → add  `AmazonS3FullAccess`
    
    ![Untitled](https://github.com/dougieduk/kafka_stock_data_collection_project/blob/main/resources_for_md/images/Untitled1.png)
    
4. Create User
5. `IAM` → `Users` → `{user_name}` → `Access Keys` → `Create Access Keys` → `Command Line Interface (CLI)`
6. `Download .csv` : keep the secret key & the access key 

### 3. Set Up AWS CLI

1. Setting up the AWS CLI allows `s3fs` library to access the s3 directories as a local directory
2. `aws configure` → add the keys from previous step 
    
    ![Untitled](https://github.com/dougieduk/kafka_stock_data_collection_project/blob/main/resources_for_md/images/Untitled2.png)
    

# Complete the Code and Check the data

### 1. Set the Consumer to save a Parquet File with 10 rows each

```python
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
        with s3.open(f"s3://kafka-stock-data-trial/stock_market_data_\
        {current_timestamp}.parquet", "wb") as file:
            print(table)
            pq.write_table(table, file)    
            #Renew the list 
            tmp_data = [] 
```

parquet tables look like this: 

![Untitled](https://github.com/dougieduk/kafka_stock_data_collection_project/blob/main/resources_for_md/images/Untitled3.png)

and the files are saved as below: 

![Untitled](https://github.com/dougieduk/kafka_stock_data_collection_project/blob/main/resources_for_md/images/Untitled4.png)

### 2. Create Glue Crawler

1. `Glue` → `Data Catalog` → `Crawlers` → `Create Crawler` 
2. Enter Crawler Name → `Next` 
3. Select `Not Yet` for `Is your data already mapped to Glue tables?` → `Add a data source` → select your bucket for `S3 Path` → `Add an S3 data Source` → `Next` 
4. Choose IAM role → (If None) click `Create new IAM role` → `Next` 
5. `Add database` → select the created database → Click `Advanced options` 
    
    ![Untitled](https://github.com/dougieduk/kafka_stock_data_collection_project/blob/main/resources_for_md/images/Untitled5.png)
    
6. `Crawler Schedule` : On demand 
7. `Create Cralwer` 

### 3. Run Crawler

Click `Run Crawler` and wait until the crawler finishes 

### 4. Query the Table in Athena

1. `Athena` → `Settings` → `Manage` → add a S3 bucket to save temporary query results 
2. `Editor` → `Tables and views` : find the table name you put in previous steps 
    
    ![Untitled](https://github.com/dougieduk/kafka_stock_data_collection_project/blob/main/resources_for_md/images/Untitled6.png)
    
3. Query & Check the data!
    
    ![Untitled](https://github.com/dougieduk/kafka_stock_data_collection_project/blob/main/resources_for_md/images/Untitled7.png)
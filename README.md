
# **Publish Subscribe System**

## **Project Structure**

```
.
├── broker.py        # Broker code to manage topics, subscriptions, and handle gossip protocol
├── subscriber.py    # Subscriber code that subscribes to topics using long polling
└── publisher.py     # Publisher code to publish messages to topics
```

## **Steps to Run the Code**

1. **Hosting**:
     This project can be hosted both in local and cloud machines.

1. **Install Dependencies and Set up Global State**:
   - Ensure you have Python installed on your machine.
   - Since the global state is needed for the bully algorithm, add the addresses of the nodes as 'ip-address,port' in the globalState.csv file.
     ```bash
     localhost,3000
     localhost,3001
     ```

2. **Running the Brokers**:
   - **Broker 1**:
     Open a terminal and run the first broker:
     ```bash
     cd brokers
     python3 broker.py --host localhost --port 3000
     ```
   
   - **Broker 2**:
     Open another terminal and run the second broker:
     ```bash
     cd brokers
     python3 broker.py --host localhost --port 3001
     ```

   This starts two brokers that will synchronize topics and messages using the gossip protocol.

3. **Running the Subscriber**:
   Open a new terminal and run the subscriber:
   ```bash
   python3 subscriber.py --host localhost --port 3001
   ```
   - Provide the ip-address and port of the broker to which the subscriber should subscribe to.

4. **Running the Publisher**:
   Open another terminal and run the publisher:
   ```bash
   python3 publisher.py --host localhost --port 3000
   ```
   - Provide the ip-address and port of the broker to which the publisher should publish to.
     
## **Features Implemented**

### **Multiple Brokers**:
- The system supports **multiple brokers** to allow for greater scalability and fault tolerance.
- Brokers run independently on different ports and can communicate with each other to synchronize their state using the **gossip protocol**.
- Each broker can have multiple **subscribers** and **publishers**, and they all share topics and messages.

### **Gossip Protocol**:
- The **gossip protocol** allows brokers to synchronize topics and their corresponding messages across different brokers.
- Brokers exchange gossip information to all other brokers whenever it receives a new message.
- When a broker receives a gossip message that is already stored in its database, it does not gossip that message to the other brokers, thus ensuring that the gossip is not infinite.

### **Leader Election**:
- A leader or coordinator is elected by comparing the **ip-address:port** using the bully algorithm.
- The bully algorithm has been implemented in such a way that whenever a new broker is up, it initiates election.

### **Lamport Timestamps**:
- Lamport timestamps help establish causality of the data arriving at each node.
- Except for the messages that get gossiped between the brokers, every instruction, send, and receive operation is considered as an event to increment timestamps.

### **Database**:
- The system uses **SQLite** to store and persist topics and their corresponding messages in a database file called `broker.db`.
- Every broker maintains an SQLite database where it stores all the topics and their latest messages. When a new message is published, the broker updates its database.


# **Pub-Sub System with Gossip Protocol and Long Polling**

## **Project Structure**

```
.
├── broker.py        # Broker code to manage topics, subscriptions, and handle gossip protocol
├── subscriber.py    # Subscriber code that subscribes to topics using long polling
├── publisher.py     # Publisher code to publish messages to topics
└── broker.db        # SQLite database file for storing topics and messages
```

## **Steps to Run the Code**

1. **Install Dependencies**:
   - Ensure you have Python installed on your machine.
   - This project uses only the standard Python library, so no additional packages are required.

2. **Running the Brokers**:
   - **Broker 1**:
     Open a terminal and run the first broker:
     ```bash
     cd brokers
     python3 broker.py --host localhost --port 3000 --peers localhost:3001
     ```
   
   - **Broker 2**:
     Open another terminal and run the second broker:
     ```bash
     cd brokers
     python3 broker.py --host localhost --port 3001 --peers localhost:3000
     ```

   - This starts two brokers that will synchronize topics and messages using the **gossip protocol**.

   Understanding Peer Connections

	•	The --peers argument specifies the list of peer brokers in the format host:port.
	•	When the broker starts, it attempts to gossip with these peers.

   ```bash
   python3 broker.py --host 192.168.1.10 --port 3000 --peers 192.168.1.11:3001 203.0.113.5:3002
   ```





3. **Running the Subscriber**:
   Open a new terminal and run the subscriber:
   ```bash
   python3 subscriber.py
   ```
   - The subscriber will prompt you to enter a topic to subscribe to. It will then wait for updates from the broker.

4. **Running the Publisher**:
   Open another terminal and run the publisher:
   ```bash
   python3 publisher.py
   ```
   - The publisher will prompt you to enter a topic and message. It will then publish the message to the broker, which will broadcast it to all subscribers.

## **Features Implemented**

### **Multiple Brokers**:
- The system supports **multiple brokers** to allow for greater scalability and fault tolerance.
- Brokers run independently on different ports and can communicate with each other to synchronize their state using the **gossip protocol**.
- Each broker can have multiple **subscribers** and **publishers**, and they all share topics and messages.

### **Gossip Protocol**:
- The **gossip protocol** allows brokers to **synchronize topics** and their corresponding messages across different brokers.
- Brokers periodically **gossip** with other brokers, exchanging information about their topics and messages.
- If a broker has a more recent version of a topic, it synchronizes its state with the peer broker.
- This ensures that **all brokers** have the same up-to-date version of topics and messages, even if a message was published on a different broker.

#### **How Gossip Protocol Works**:
1. Each broker maintains a list of **peers** (other brokers it communicates with).
2. Every broker **periodically gossips** with its peers by sending a **sync message** that includes the current state of its topics.
3. If a broker receives a **new topic** or a **more recent message** for a topic, it updates its local state.
4. This process allows for eventual consistency between brokers.

### **Long Polling**:
- **Long polling** is used to allow **subscribers** to receive updates for a topic in real-time.
- When a subscriber subscribes to a topic, the broker keeps the connection open until a new message is available for that topic.
- If a new message is published for a subscribed topic, the broker sends it to the subscriber.
- The subscriber remains connected and continues to receive updates as long as they remain subscribed.

#### **How Long Polling Works**:
1. The **subscriber** sends a request to the broker to subscribe to a topic.
2. The broker keeps the connection open and waits for a message to be published for the subscribed topic.
3. Once a new message is published, the broker sends the message to the waiting subscriber.
4. The subscriber receives the message and can continue to wait for further updates.

### **Database**:
- The system uses **SQLite** to store and persist topics and their corresponding messages in a database file called `broker.db`.
- **Broker Database**: The broker maintains a SQLite database where it stores all the topics and their latest messages. When a new message is published, the broker updates the database to ensure data persistence.
- The database is especially useful for recovering the state of topics in case the broker restarts. Upon startup, the broker loads the topics and their messages from the database into memory, ensuring that subscribers receive the correct information.

---

## **Usage Example**

1. **Start Broker 1**:
   ```bash
   cd brokers
   python3 broker.py --host localhost --port 2000 --peers localhost:2001
   ```

2. **Start Broker 2**:
   ```bash
   cd brokers
   python3 broker.py --host localhost --port 2001 --peers localhost:2000
   ```

3. **Start Subscriber**:
   ```bash
   cd subscribers
   python3 subscriber.py
   ```
   You will be prompted to subscribe to a topic (e.g., `news`).

4. **Start Publisher**:
   ```bash
   cd publishers
   python3 publisher.py
   ```
   Enter a topic and message, and the message will be sent to the broker and broadcasted to all subscribers.

---

## **Author**:
**Manasa Deshagouni**

---

### **Additional Notes**:

- **Gossip Protocol** ensures that all brokers stay synchronized with the latest messages and topics, so even if one broker is down, the others will have consistent data.
- **Long Polling** provides real-time communication between the broker and subscribers, so subscribers get updates as soon as they are available.


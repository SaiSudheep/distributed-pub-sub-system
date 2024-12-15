import socket
import threading
import json
import sqlite3
import argparse
import time

class Broker:
    def __init__(self, host, port, global_state_file):
        self.host = host
        self.port = port
        self.peers = self.load_peers(global_state_file)
        self.topics = {}  # topic -> latest message
        self.subscribers = {}  # topic -> list of subscriber connections
        self.isCoordinator = False  # Leader election flag
        self.coordinator = None  # Tracks the current coordinator
        self.db_file = "broker.db"  # SQLite database file
        self.lamport_timestamp = 0
        self.init_database()

        # Trigger leader election upon deployment
        threading.Thread(target=self.initiate_election, daemon=True).start()

    def load_peers(self, global_state_file):
        """Load peers from the provided CSV file."""
        peers = []
        try:
            with open(global_state_file, 'r') as file:
                lines = file.readlines()
                for line in lines[1:]:  # Skip the header
                    ip, port = line.strip().split(',')
                    if (ip, int(port)) != (self.host, self.port):  # Avoid adding itself
                        peers.append((ip, int(port)))
        except Exception as e:
            print(f"Error loading peers from {global_state_file}: {e}")
        return peers

    def init_database(self):
        """Initialize the database for storing topics and messages."""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS topics (
                    topic TEXT PRIMARY KEY,
                    latest_message TEXT
                )
            """)
            conn.commit()
            conn.close()
            print("Database initialized.")
        except Exception as e:
            print(f"Database initialization failed: {e}\n")

    def initiate_election(self):
        """Initiate the leader election process."""
        print(f"Broker at {self.host}:{self.port} initiating election.")
        self.lamport_timestamp += 1
        print(f"Lamport Timestamp: {self.lamport_timestamp}\n")
        higher_priority_peers = [
            peer for peer in self.peers
            if (peer[0], peer[1]) > (self.host, self.port)
        ]

        responses = []

        def send_election(peer):
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect(peer)
                message = {"type": "election", "sender": (self.host, self.port), "lamport_timestamp": self.lamport_timestamp}
                s.send(json.dumps(message).encode('utf-8'))
                s.settimeout(5)
                response = s.recv(1024)
                responses.append(json.loads(response.decode('utf-8')))
                s.close()
            except Exception as e:
                pass
                # print(f"Failed to communicate with peer {peer}: {e}\n")

        # Send election messages to higher-priority peers
        threads = []
        for peer in higher_priority_peers:
            self.lamport_timestamp += 1
            thread = threading.Thread(target=send_election, args=(peer,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        print(f"Election messages sent to {len(higher_priority_peers)} higher id broker(s) by {self.host}:{self.port}")
        print(f"Lamport Timestamp: {self.lamport_timestamp}\n")
        if not responses:
            # No responses, elect self as coordinator
            self.announce_coordinator()
        else:
            print(f"Broker at {self.host}:{self.port} waiting for a coordinator.")

    def announce_coordinator(self):
        """Announce that this broker is the new coordinator."""
        print(f"Broker at {self.host}:{self.port} is the new coordinator.")
        self.isCoordinator = True
        self.coordinator = (self.host, self.port)

        # Notify all peers
        for peer in self.peers:
            self.lamport_timestamp += 1
            self.send_message(peer, {
                "type": "coordinator",
                "sender": (self.host, self.port),
                "lamport_timestamp": self.lamport_timestamp
            })
        
        print(f"Notifications sent out to {len(self.peers)} brokers about new coordinator.")
        print(f"Lamport Timestamp: {self.lamport_timestamp}\n")

    def handle_client(self, conn, addr):
        """Handle incoming client connections."""
        # print(f"Connected to {addr}")
        while True:
            try:
                data = conn.recv(1024)
                if not data:
                    break
                message = json.loads(data.decode('utf-8'))
                self.process_message(message, conn)
            except Exception as e:
                print(f"Error handling client {addr}: {e}")
                break
        conn.close()
        # print(f"Disconnected from {addr}\n")

    def process_message(self, message, conn):
        """Process incoming messages based on their type."""
        message_type = message.get("type")

        if message_type == "publish":
            self.handle_publish_message(message, conn)
        elif message_type == "subscribe":
            self.handle_subscribe_message(message, conn)
        elif message_type == "gossip":
            self.handle_gossip_message(message)
        elif message_type == "election":
            self.handle_election_message(message, conn)
        elif message_type == "coordinator":
            self.handle_coordinator_message(message)

    def handle_election_message(self, message, conn):
        """Handle election messages."""
        sender = message.get("sender")
        self.lamport_timestamp = max(message.get("lamport_timestamp"), self.lamport_timestamp) + 1
        print(f"Received election message from {sender}")
        print(f"Lamport Timestamp: {self.lamport_timestamp}\n")

        # Acknowledge receipt of the election message
        response = {"type": "election_ack", "ack": True}
        conn.send(json.dumps(response).encode('utf-8'))

        # If the sender has lower priority, initiate a new election
        if self.is_higher_priority(sender):
            self.initiate_election()

    def handle_coordinator_message(self, message):
        """Handle coordinator announcements."""
        self.coordinator = message.get("sender")
        self.lamport_timestamp = max(message.get("lamport_timestamp"), self.lamport_timestamp) + 1
        print(f"New coordinator is {self.coordinator}")
        print(f"Lamport Timestamp: {self.lamport_timestamp}\n")
        self.isCoordinator = (self.coordinator == (self.host, self.port))

    def handle_publish_message(self, message, conn):
        """Handle publish requests."""
        topic = message.get("topic")
        msg = message.get("message")
        self.lamport_timestamp = max(message.get("lamport_timestamp"), self.lamport_timestamp) + 1
        print(f"New data has been published - {self.host}:{self.port} initiating gossip")
        print(f"Lamport Timestamp: {self.lamport_timestamp}\n")
        self.topics[topic] = msg
        self.update_database(topic, msg)

        # Notify subscribers
        if topic in self.subscribers:
            for subscriber in self.subscribers[topic]:
                try:
                    subscriber.send(json.dumps({"type": "publish", "topic": topic, "message": msg, "lamport_timestamp": self.lamport_timestamp}).encode('utf-8'))
                except Exception as e:
                    print(f"Error notifying subscriber: {e}")

        # Gossip this message to peers
        self.gossip_message(topic, msg)

    def handle_subscribe_message(self, message, conn):
        """Handle subscription requests."""
        topic = message.get("topic")
        self.lamport_timestamp += 1
        if topic not in self.subscribers:
            self.subscribers[topic] = []
        self.subscribers[topic].append(conn)
        print(f"Subscriber added for topic: {topic}")
        print(f"Lamport Timestamp: {self.lamport_timestamp}\n")

    def handle_gossip_message(self, message):
        """Handle gossip messages from other brokers."""
        topic = message.get("topic")
        msg = message.get("message")

        # Check if the topic already exists in the database
        if not self.is_message_in_database(topic, msg):
            print(f"New data has arrived through gossip - {self.host}:{self.port} forwarding gossip")
            self.lamport_timestamp = max(message.get("lamport_timestamp"), self.lamport_timestamp) + 1
            print(f"Lamport Timestamp: {self.lamport_timestamp}\n")
            self.topics[topic] = msg
            self.update_database(topic, msg)

            # Notify subscribers
            if topic in self.subscribers:
                for subscriber in self.subscribers[topic]:
                    try:
                        subscriber.send(json.dumps({"type": "publish", "topic": topic, "message": msg, "lamport_timestamp": self.lamport_timestamp}).encode('utf-8'))
                    except Exception as e:
                        print(f"Error notifying subscriber: {e}")

            # Gossip the message further
            self.gossip_message(topic, msg)
        else:
            print(f"Data already stored in DB - {self.host}:{self.port} already received gossip")

    def is_message_in_database(self, topic, message):
        """Check if the topic and message already exist in the database."""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute("SELECT latest_message FROM topics WHERE topic = ?", (topic,))
            row = cursor.fetchone()
            conn.close()
            return row is not None and row[0] == message
        except Exception as e:
            print(f"Database query failed: {e}")
            return False

    def update_database(self, topic, message):
        """Update topic data in the database."""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO topics (topic, latest_message)
                VALUES (?, ?)
            """, (topic, message))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Database update failed: {e}")

    def gossip_message(self, topic, message):
        """Gossip a message to all peers."""
        for peer in self.peers:
            self.send_message(peer, {
                "type": "gossip",
                "topic": topic,
                "message": message,
                "lamport_timestamp": self.lamport_timestamp
            })

    def send_message(self, peer, message):
        """Send a message to a peer."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(peer)
            s.send(json.dumps(message).encode('utf-8'))
            s.close()
        except Exception as e:
            pass
            # print(f"Failed to send message to {peer}: {e}\n")

    def is_higher_priority(self, sender):
        """Determine if this broker has higher priority than the sender."""
        sender_host, sender_port = sender
        return (self.host, self.port) > (sender_host, sender_port)

    def start(self):
        """Start the broker server."""
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(('0.0.0.0', self.port))
        server.listen(5)
        # print(f"Broker running on {self.host}:{self.port}")
        try:
            while True:
                conn, addr = server.accept()
                threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True).start()
        except Exception as e:
            print(f"{e}")
        finally:
            """Gracefully shut down the broker server."""
            print(f"Shutting down the broker server at {self.host}:{self.port}...")
            server.close()
            sys.exit(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Broker for publish-subscribe system with leader election.")
    parser.add_argument("--host", type=str, required=True, help="Host IP address of the broker.")
    parser.add_argument("--port", type=int, required=True, help="Port number of the broker.")
    args = parser.parse_args()

    GLOBAL_STATE_FILE = "globalState.csv"  # File containing peer information

    broker = Broker(args.host, args.port, GLOBAL_STATE_FILE)
    broker.start()

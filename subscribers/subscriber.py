import socket
import json
import argparse


class Subscriber:
    def __init__(self, broker_host, broker_port):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.lamport_timestamp = 0

    def subscribe(self, topic):
        """Subscribe to a topic and print updates."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                print(f"Connecting to broker at {self.broker_host}:{self.broker_port}...")
                s.connect((self.broker_host, self.broker_port))
                print(f"Connected. Subscribing to topic '{topic}'...")
                self.lamport_timestamp += 1
                data = {"type": "subscribe", "topic": topic.lower(), "lamport_timestamp": self.lamport_timestamp}
                s.send(json.dumps(data).encode('utf-8'))  # Send data as JSON string
                while True:
                    message_data = s.recv(1024)
                    if message_data:
                        message = json.loads(message_data.decode('utf-8'))  # Decode and parse JSON
                        print(f"Update on '{message['topic']}': {message['message']}")
                        self.lamport_timestamp = max(message['lamport_timestamp'], self.lamport_timestamp) + 1
                        print(f"Lamport Timestamp: {self.lamport_timestamp}\n")
        except Exception as e:
            print(f"Error subscribing to topic: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Subscriber client.")
    parser.add_argument('--host', type=str, required=True, help="Broker host address (e.g., 'localhost').")
    parser.add_argument('--port', type=int, required=True, help="Broker port number (e.g., 2001).")
    parser.add_argument('--topic', type=str, default="stocks", help="Topic to subscribe to (default: 'stocks').")
    
    args = parser.parse_args()
    
    subscriber = Subscriber(args.host, args.port)
    subscriber.subscribe(args.topic)
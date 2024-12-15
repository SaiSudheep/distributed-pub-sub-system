import socket
import json
import time
import argparse


class Publisher:
    def __init__(self, broker_host, broker_port):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.lamport_timestamp = 0

    def publish(self, topic, message):
        """Publish a message to a topic."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                print(f"Connecting to broker at {self.broker_host}:{self.broker_port}...")
                s.connect((self.broker_host, self.broker_port))
                print(f"Connected. Publishing to topic '{topic}'...")
                self.lamport_timestamp += 1
                data = {"type": "publish", "topic": topic.lower(), "message": message, "lamport_timestamp": self.lamport_timestamp}
                s.send(json.dumps(data).encode('utf-8'))  # Send data as JSON string
                print(f"Publishing data:\n{data}\n")
        except Exception as e:
            print(f"Error publishing message: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Publisher client.")
    parser.add_argument('--host', type=str, required=True, help="Broker host address (e.g., 'localhost').")
    parser.add_argument('--port', type=int, required=True, help="Broker port number (e.g., 2000).")
    parser.add_argument('--topic', type=str, default="stocks", help="Topic to publish to (default: 'stocks').")
    
    args = parser.parse_args()

    publisher = Publisher(args.host, args.port)
    message = f"Stock update at {time.ctime()}"
    publisher.publish(args.topic, message)
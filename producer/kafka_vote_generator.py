import json
import random
import time
from datetime import datetime

from kafka import KafkaProducer


BROKER = "localhost:9092"
TOPIC = "civic-events"

candidates = [
    "Candidate A",
    "Candidate B",
    "Candidate C"
]

constituencies = [
    "Delhi",
    "Mumbai",
    "Kolkata",
    "Chennai"
]


producer = KafkaProducer(
    bootstrap_servers=BROKER,
    value_serializer=lambda value: json.dumps(value).encode("utf-8")
)


try:
    while True:

        event = {
            "voter_id": random.randint(1, 1000),
            "candidate": random.choice(candidates),
            "constituency": random.choice(constituencies),
            "timestamp": datetime.now().isoformat()
        }

        future = producer.send(TOPIC, value=event)
        future.get(timeout=10)

        print(f"Event sent: {event}")

        time.sleep(2)

except KeyboardInterrupt:
    print("\nVote generator stopped.")

finally:
    producer.close()
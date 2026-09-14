import json
from kafka import KafkaProducer

BROKER = "localhost:9092"
TOPIC = "civic-events"


def create_producer():
    return KafkaProducer(
        bootstrap_servers=BROKER,
        value_serializer=lambda value: json.dumps(value).encode("utf-8")
    )


def send_event(producer, event):
    future = producer.send(TOPIC, value=event)
    future.get(timeout=10)


if __name__ == "__main__":
    producer = create_producer()

    test_event = {
        "voter_id": 1,
        "candidate": "Candidate A",
        "constituency": "Kanpur",
        "timestamp": "2026-09-14T12:00:00"
    }

    try:
        send_event(producer, test_event)
        print("Event sent successfully to Kafka")

    except Exception as e:
        print(f"Failed to send event: {e}")

    finally:
        producer.close()
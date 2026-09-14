import json
from kafka import KafkaConsumer

BROKER = "localhost:9092"
TOPIC = "civic-events"


def create_consumer():
    return KafkaConsumer(
        TOPIC,
        bootstrap_servers=BROKER,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        group_id="civicsense-consumer",
        value_deserializer=lambda value: json.loads(value.decode("utf-8"))
    )


if __name__ == "__main__":
    consumer = create_consumer()

    print(f"Listening for events on '{TOPIC}'...")

    try:
        for message in consumer:
            print("Received event:")
            print(message.value)

    except KeyboardInterrupt:
        print("\nConsumer stopped.")

    finally:
        consumer.close()
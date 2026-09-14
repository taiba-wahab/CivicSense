"""
CivicSense - Python Event Generator
===================================

Generates synthetic real-time voting events.

Pipeline:
    Python Event Generator
            ↓
        Apache Kafka
            ↓
     Spark Streaming
            ↓
       PostgreSQL
            ↓
       Streamlit

The generator supports:
    1. Console output
    2. JSONL file output
    3. Kafka streaming

Configuration:
    Kafka settings are read from the .env file.

Example .env:
    KAFKA_BOOTSTRAP_SERVERS=localhost:9092
    KAFKA_TOPIC=civic-events
"""

import argparse
import json
import os
import random
import time
import uuid
from datetime import datetime, timezone

from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

KAFKA_BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP_SERVERS",
    "localhost:9092"
)

KAFKA_TOPIC = os.getenv(
    "KAFKA_TOPIC",
    "civic-events"
)


# ---------------------------------------------------------------------------
# Optional Faker
# ---------------------------------------------------------------------------

try:
    from faker import Faker

    fake = Faker()

except ImportError:
    fake = None


# ---------------------------------------------------------------------------
# Synthetic election reference data
# ---------------------------------------------------------------------------

CANDIDATES = [
    {
        "id": "C1",
        "name": "Alex Rivera",
        "party": "Progress Party"
    },
    {
        "id": "C2",
        "name": "Jordan Blake",
        "party": "Unity Alliance"
    },
    {
        "id": "C3",
        "name": "Sam Okafor",
        "party": "Green Future"
    },
    {
        "id": "C4",
        "name": "Taylor Chen",
        "party": "Liberty Coalition"
    },
]

STATES = [
    "California",
    "Texas",
    "New York",
    "Florida",
    "Illinois",
    "Pennsylvania",
    "Ohio",
    "Georgia",
    "North Carolina",
    "Michigan",
]

AGE_GROUPS = [
    "18-24",
    "25-34",
    "35-44",
    "45-54",
    "55-64",
    "65+",
]

VOTING_METHODS = [
    "in_person",
    "mail_in",
    "early_voting",
]

FIRST_NAMES = [
    "Aarav",
    "Priya",
    "James",
    "Maria",
    "Wei",
    "Fatima",
    "Liam",
    "Sofia",
    "Noah",
    "Emma",
]

LAST_NAMES = [
    "Sharma",
    "Smith",
    "Garcia",
    "Khan",
    "Müller",
    "Kim",
    "Rossi",
    "Johnson",
    "Patel",
    "Nguyen",
]


# ---------------------------------------------------------------------------
# Generate synthetic voter name
# ---------------------------------------------------------------------------

def generate_voter_name():
    """
    Generate a synthetic voter name.

    Faker is used when installed.
    Otherwise, a predefined list is used.
    """

    if fake:
        return fake.name()

    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


# ---------------------------------------------------------------------------
# Generate one voting event
# ---------------------------------------------------------------------------

def generate_voter_event():
    """
    Generate one synthetic voting event.

    Returns:
        dict: JSON-serializable voting event.
    """

    candidate = random.choice(CANDIDATES)

    event = {
        "event_id": str(uuid.uuid4()),
        "voter_id": str(uuid.uuid4()),
        "voter_name": generate_voter_name(),
        "age_group": random.choice(AGE_GROUPS),
        "state": random.choice(STATES),
        "candidate_id": candidate["id"],
        "candidate_name": candidate["name"],
        "party": candidate["party"],
        "voting_method": random.choice(VOTING_METHODS),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    return event


# ---------------------------------------------------------------------------
# Kafka producer
# ---------------------------------------------------------------------------

def get_kafka_producer(bootstrap_servers):
    """
    Create a Kafka producer.

    Kafka is imported only when Kafka mode is requested.
    """

    try:
        from kafka import KafkaProducer

    except ImportError:
        raise RuntimeError(
            "kafka-python is not installed. "
            "Run: pip install kafka-python"
        )

    producer = KafkaProducer(
        bootstrap_servers=bootstrap_servers.split(","),
        value_serializer=lambda value: json.dumps(value).encode("utf-8"),
        key_serializer=lambda key: key.encode("utf-8") if key else None,
    )

    return producer


# ---------------------------------------------------------------------------
# Run generator
# ---------------------------------------------------------------------------

def run(args):

    producer = None
    output_file = None
    sent = 0

    # -------------------------------------------------------
    # Kafka setup
    # -------------------------------------------------------

    if args.kafka:

        try:
            producer = get_kafka_producer(
                args.bootstrap_servers
            )

            # Force a connection check
            producer.bootstrap_connected()

            print(
                f"Connected to Kafka: "
                f"{args.bootstrap_servers}"
            )

            print(
                f"Kafka topic: {args.topic}"
            )

        except Exception as error:

            print("\nERROR: Could not connect to Kafka.")
            print(f"Kafka server: {args.bootstrap_servers}")
            print(f"Details: {error}")

            print(
                "\nMake sure Kafka is running and "
                "the broker is available."
            )

            return

    # -------------------------------------------------------
    # File setup
    # -------------------------------------------------------

    if args.output:

        output_file = open(
            args.output,
            "a",
            encoding="utf-8"
        )

        print(
            f"Writing events to: {args.output}"
        )

    # -------------------------------------------------------
    # Event generation rate
    # -------------------------------------------------------

    if args.rate > 0:
        interval = 1.0 / args.rate
    else:
        interval = 0

    print("\nCivicSense Event Generator Started")
    print("-----------------------------------")
    print(f"Rate: {args.rate} events/sec")

    if args.count:
        print(f"Target events: {args.count}")
    else:
        print("Target events: Unlimited")

    print()

    try:

        while True:

            event = generate_voter_event()

            json_event = json.dumps(event)

            # ------------------------------------------------
            # Send to Kafka
            # ------------------------------------------------

            if producer:

                future = producer.send(
                    args.topic,
                    key=event["voter_id"],
                    value=event
                )

                # Wait for Kafka acknowledgement
                future.get(timeout=10)

            # ------------------------------------------------
            # Save to file
            # ------------------------------------------------

            if output_file:

                output_file.write(
                    json_event + "\n"
                )

                output_file.flush()

            # ------------------------------------------------
            # Console output
            # ------------------------------------------------

            if args.print_events:

                print(json_event)

            sent += 1

            # ------------------------------------------------
            # Stop after requested count
            # ------------------------------------------------

            if args.count and sent >= args.count:
                break

            # ------------------------------------------------
            # Control generation rate
            # ------------------------------------------------

            if interval:
                time.sleep(interval)

    except KeyboardInterrupt:

        print("\nGenerator stopped by user.")

    except Exception as error:

        print(
            f"\nERROR while generating events: {error}"
        )

    finally:

        if producer:

            try:
                producer.flush()
                producer.close()

            except Exception:
                pass

        if output_file:
            output_file.close()

        print(
            f"\nTotal events generated: {sent}"
        )


# ---------------------------------------------------------------------------
# Command-line arguments
# ---------------------------------------------------------------------------

def parse_args():

    parser = argparse.ArgumentParser(
        description=(
            "CivicSense synthetic real-time "
            "voting event generator"
        )
    )

    parser.add_argument(
        "--rate",
        type=float,
        default=1.0,
        help=(
            "Events generated per second. "
            "Default: 1"
        ),
    )

    parser.add_argument(
        "--count",
        type=int,
        default=0,
        help=(
            "Number of events to generate. "
            "0 means run forever."
        ),
    )

    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help=(
            "Save events to a JSONL file."
        ),
    )

    parser.add_argument(
        "--kafka",
        action="store_true",
        help=(
            "Send generated events to Kafka."
        ),
    )

    parser.add_argument(
        "--bootstrap-servers",
        type=str,
        default=KAFKA_BOOTSTRAP_SERVERS,
        help=(
            "Kafka bootstrap servers. "
            "Default comes from .env."
        ),
    )

    parser.add_argument(
        "--topic",
        type=str,
        default=KAFKA_TOPIC,
        help=(
            "Kafka topic. "
            "Default comes from .env."
        ),
    )

    parser.add_argument(
        "--print-events",
        action="store_true",
        help=(
            "Print generated events to the console."
        ),
    )

    return parser.parse_args()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    run(parse_args())
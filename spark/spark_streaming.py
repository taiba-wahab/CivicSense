from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, to_timestamp
from pyspark.sql.types import StructType, StructField, StringType

import os
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv


# Load environment variables
load_dotenv()


# -----------------------------
# Create Spark session
# -----------------------------

spark = (
    SparkSession.builder
    .appName("CivicSenseStreaming")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")


# -----------------------------
# Define incoming Kafka schema
# -----------------------------

schema = StructType([
    StructField("candidate", StringType(), True),
    StructField("constituency", StringType(), True),
    StructField("timestamp", StringType(), True)
])


# -----------------------------
# Read events from Kafka
# -----------------------------

kafka_df = (
    spark.readStream
    .format("kafka")
    .option("kafka.bootstrap.servers", "localhost:9092")
    .option("subscribe", "civic-events")
    .option("startingOffsets", "latest")
    .load()
)


# -----------------------------
# Convert Kafka value to JSON
# -----------------------------

json_df = kafka_df.select(
    col("value").cast("string").alias("json_data")
)


# -----------------------------
# Parse JSON
# -----------------------------

parsed_df = (
    json_df
    .select(
        from_json(col("json_data"), schema).alias("data")
    )
    .select(
    "candidate",
    "constituency",
    "timestamp"
)
)


# -----------------------------
# Convert timestamp
# -----------------------------

processed_df = parsed_df.withColumn(
    "vote_time",
    to_timestamp(col("timestamp"))
).drop("timestamp")


# -----------------------------
# Write each Spark batch
# to PostgreSQL
# -----------------------------

def write_to_postgres(batch_df, batch_id):

    rows = batch_df.select(
        "candidate",
        "constituency",
        "vote_time"
    ).collect()

    if not rows:
        return

    connection = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.getenv("DB_NAME", "CivicSense"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD")
    )

    cursor = connection.cursor()

    values = [
        (
            row["candidate"],
            row["constituency"],
            row["vote_time"]
        )
        for row in rows
    ]

    execute_values(
        cursor,
        """
        INSERT INTO votes
        (candidate, constituency, vote_time)
        VALUES %s
        """,
        values
    )

    connection.commit()

    cursor.close()
    connection.close()

    print(
        f"Batch {batch_id}: "
        f"{len(values)} events written to PostgreSQL"
    )


# -----------------------------
# Start streaming query
# -----------------------------

query = (
    processed_df.writeStream
    .foreachBatch(write_to_postgres)
    .outputMode("append")
    .option(
        "checkpointLocation",
        "./spark_checkpoint"
    )
    .start()
)


query.awaitTermination()
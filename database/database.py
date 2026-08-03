import psycopg2


def get_connection():

    connection = psycopg2.connect(
        host="localhost",
        database="CivicSense",
        user="postgres",
        password="civicPASS",
        port="5432"
    )

    return connection
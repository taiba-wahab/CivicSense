import random
import time
from datetime import datetime

from database.database import get_connection


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


def insert_vote(candidate, constituency, vote_time):

    connection = get_connection()

    cursor = connection.cursor()

    query = """
    INSERT INTO votes(candidate, constituency, vote_time)
    VALUES (%s, %s, %s)
    """

    cursor.execute(
        query,
        (candidate, constituency, vote_time)
    )

    connection.commit()

    cursor.close()
    connection.close()


while True:

    candidate = random.choice(candidates)
    constituency = random.choice(constituencies)
    vote_time = datetime.now()

    insert_vote(
        candidate,
        constituency,
        vote_time
    )

    print(
        f"Vote generated: {candidate} from {constituency}"
    )

    time.sleep(2)
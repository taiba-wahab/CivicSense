from streamlit_autorefresh import st_autorefresh
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine


# Database connection
engine = create_engine(
    "postgresql://postgres:civicPASS@localhost:5432/CivicSense"
)


st.title("CivicSense: Live Election Dashboard")


# Auto refresh every 5 seconds
st_autorefresh(
    interval=5000,
    key="vote_refresh"
)


# Fetch votes
query = """
SELECT * FROM votes;
"""

df = pd.read_sql(query, engine)


# Total votes
total_votes = len(df)

st.metric(
    "Total Votes",
    total_votes
)


# Candidate count
st.subheader("Votes by Candidate")

candidate_count = (
    df["candidate"]
    .value_counts()
)


st.bar_chart(candidate_count)


# Constituency count
st.subheader("Votes by Constituency")

constituency_count = (
    df["constituency"]
    .value_counts()
)

st.bar_chart(constituency_count)


# Winner
winner = candidate_count.idxmax()

st.success(
    f"Current Leading Candidate: {winner}"
)
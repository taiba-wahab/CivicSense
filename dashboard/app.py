import os

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine
from dotenv import load_dotenv
from streamlit_autorefresh import st_autorefresh

load_dotenv()

# -----------------------------
# Page configuration
# -----------------------------
st.set_page_config(
    page_title="CivicSense Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("CivicSense: Live Election Dashboard")
st.caption("Real-time civic event monitoring and analytics")

# Refresh dashboard every 5 seconds
st_autorefresh(
    interval=5000,
    key="vote_refresh"
)

# -----------------------------
# Database connection
# -----------------------------
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "CivicSense")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD")

engine = create_engine(
    f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# -----------------------------
# Fetch data
# -----------------------------
query = """
SELECT id, candidate, constituency, vote_time
FROM votes
ORDER BY vote_time DESC;
"""

try:
    df = pd.read_sql(query, engine)

except Exception as e:
    st.error("Unable to connect to the CivicSense database.")
    st.exception(e)
    st.stop()

# -----------------------------
# Empty database
# -----------------------------
if df.empty:
    st.info("No votes available yet. Waiting for streaming data...")

    st.markdown(
        """
        ### System Status

        🟢 **Dashboard:** Running
	🟢 **PostgreSQL:** Connected
        🟡 **Streaming data:** Waiting for events
        """
    )

    st.stop()

# -----------------------------
# Prepare data
# -----------------------------
df["vote_time"] = pd.to_datetime(df["vote_time"])

total_votes = len(df)
candidate_count = df["candidate"].nunique()
constituency_count = df["constituency"].nunique()

candidate_votes = df["candidate"].value_counts()

leader = candidate_votes.index[0]
leader_votes = candidate_votes.iloc[0]

leader_percentage = (leader_votes / total_votes) * 100

# -----------------------------
# Top metrics
# -----------------------------
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total Votes",
        total_votes
    )

with col2:
    st.metric(
        "Candidates",
        candidate_count
    )

with col3:
    st.metric(
        "Constituencies",
        constituency_count
    )

with col4:
    st.metric(
        "Current Leader",
        leader
    )

st.divider()

# -----------------------------
# Candidate analytics
# -----------------------------
left, right = st.columns(2)

with left:
    st.subheader("Votes by Candidate")

    st.bar_chart(candidate_votes)

with right:
    st.subheader("Vote Distribution (%)")

    percentage = (
        candidate_votes / total_votes * 100
    ).round(2)

    percentage_df = percentage.reset_index()
    percentage_df.columns = ["Candidate", "Percentage"]

    st.dataframe(
        percentage_df,
        use_container_width=True,
        hide_index=True
    )

# -----------------------------
# Voting trend
# -----------------------------
st.subheader("Voting Activity Over Time")

trend = (
    df.set_index("vote_time")
    .resample("1min")
    .size()
    .rename("Votes")
)

st.line_chart(trend)

# -----------------------------
# Leader information
# -----------------------------
st.subheader("Current Leader")

st.success(
    f"{leader} is currently leading with "
    f"{leader_votes} votes ({leader_percentage:.2f}%)."
)

# -----------------------------
# Latest events
# -----------------------------
st.subheader("Latest Voting Events")

latest_events = df.head(10).copy()

st.dataframe(
    latest_events,
    use_container_width=True,
    hide_index=True
)

# -----------------------------
# Footer
# -----------------------------
st.divider()

st.caption(
    "CivicSense • Real-time event streaming demonstration"
)
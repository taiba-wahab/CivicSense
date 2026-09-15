import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine
from dotenv import load_dotenv
from streamlit_autorefresh import st_autorefresh
import datetime

load_dotenv()

# -----------------------------
# Page configuration
# -----------------------------
st.set_page_config(
    page_title="CivicSense Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -----------------------------
# Custom CSS for Professional Look
# -----------------------------
st.markdown("""
    <style>
    /* Main background */
    .stApp {
        background-color: #f8f9fa;
    }

    /* Headers and typography */
    h1, h2, h3 {
        color: #1e293b;
        font-family: 'Inter', 'Segoe UI', sans-serif;
    }

    /* Metric Cards */
    .metric-card {
        background-color: #ffffff;
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        border-left: 5px solid #0369a1; /* professional blue */
        margin-bottom: 20px;
    }
    .metric-title {
        margin: 0;
        color: #64748b;
        font-size: 0.9rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .metric-value {
        margin: 10px 0 0 0;
        color: #0f172a;
        font-size: 2rem;
        font-weight: 700;
    }
    .metric-subtitle {
        margin: 5px 0 0 0;
        color: #475569;
        font-size: 0.85rem;
    }

    /* Clean up default Streamlit elements */
    .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------
# Header
# -----------------------------
col_logo, col_title, col_status = st.columns([0.5, 3, 1])

with col_title:
    st.markdown("<h1 style='margin-bottom: 0;'>CivicSense</h1>", unsafe_allow_html=True)
    st.markdown("<h4 style='color: #475569; margin-top: 0; font-weight: 400;'>Real-Time Civic Event Monitoring</h4>", unsafe_allow_html=True)

with col_status:
    # We will update the status indicator after checking the DB connection
    status_placeholder = st.empty()

st.markdown("<hr style='margin-top: 0.5rem; margin-bottom: 1.5rem;'/>", unsafe_allow_html=True)

# Refresh dashboard every 5 seconds
st_autorefresh(interval=5000, key="vote_refresh")

# -----------------------------
# Database connection
# -----------------------------
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "CivicSense")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD")

try:
    engine = create_engine(f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

    query = """
    SELECT id, candidate, constituency, vote_time
    FROM votes
    ORDER BY vote_time DESC;
    """
    df = pd.read_sql(query, engine)

    # Update status indicator to active since DB is connected
    current_time = datetime.datetime.now().strftime("%H:%M:%S")
    status_placeholder.markdown(
        f"""
        <div style='text-align: right; padding-top: 15px;'>
            <div style='display: inline-block; padding: 4px 12px; background-color: #dcfce7; color: #166534; border-radius: 9999px; font-size: 0.85rem; font-weight: 600; margin-bottom: 4px;'>
                🟢 STREAM ACTIVE
            </div>
            <div style='font-size: 0.75rem; color: #64748b;'>Last Refresh: {current_time}</div>
        </div>
        """,
        unsafe_allow_html=True
    )
except Exception as e:
    status_placeholder.markdown(
        """
        <div style='text-align: right; padding-top: 15px;'>
            <div style='display: inline-block; padding: 4px 12px; background-color: #fee2e2; color: #991b1b; border-radius: 9999px; font-size: 0.85rem; font-weight: 600;'>
                🔴 OFFLINE
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.error("Unable to connect to the CivicSense database. Please check your connection and credentials.")
    st.info("Ensure PostgreSQL is running and the credentials in your .env file are correct.")
    st.stop()

# -----------------------------
# Empty database handling
# -----------------------------
if df.empty:
    st.info("No voting events available yet. Waiting for streaming data to arrive...")
    st.markdown(
        """
        <div style='background-color: white; padding: 20px; border-radius: 8px; border: 1px solid #e2e8f0; margin-top: 20px;'>
            <h3 style='margin-top:0;'>System Status</h3>
            <ul style='color: #475569;'>
                <li><b>Dashboard Application:</b> Running locally via Streamlit</li>
                <li><b>PostgreSQL Database:</b> Connected successfully</li>
                <li><b>Data Stream:</b> Waiting for incoming events...</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True
    )

    # System Information Footer for empty state
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(
        """
        <div style='text-align: center; color: #94a3b8; font-size: 0.8rem; border-top: 1px solid #f1f5f9; padding-top: 20px;'>
            <strong>Data Source:</strong> PostgreSQL &nbsp; | &nbsp;
            <strong>Refresh Interval:</strong> 5 seconds &nbsp; | &nbsp;
            <strong>Application:</strong> Streamlit<br>
            CivicSense • Academic Mini-Project
        </div>
        """,
        unsafe_allow_html=True
    )
    st.stop()

# -----------------------------
# Prepare and clean data
# -----------------------------
df["vote_time"] = pd.to_datetime(df["vote_time"])

# -----------------------------
# Filters (Interactive)
# -----------------------------
st.markdown("<h3 style='margin-bottom: 10px; font-size: 1.1rem; color: #334155;'>Global Filters</h3>", unsafe_allow_html=True)
filter_col1, filter_col2 = st.columns(2)

with filter_col1:
    constituency_list = ["All"] + sorted(df["constituency"].unique().tolist())
    selected_constituency = st.selectbox("Select Constituency", constituency_list)

with filter_col2:
    candidate_list = ["All"] + sorted(df["candidate"].unique().tolist())
    selected_candidate = st.selectbox("Select Candidate", candidate_list)

# Apply filters
filtered_df = df.copy()
if selected_constituency != "All":
    filtered_df = filtered_df[filtered_df["constituency"] == selected_constituency]
if selected_candidate != "All":
    filtered_df = filtered_df[filtered_df["candidate"] == selected_candidate]

if filtered_df.empty:
    st.warning("No data available for the selected filters.")
    st.stop()

# -----------------------------
# Recalculate metrics based on filtered data
# -----------------------------
total_votes = len(filtered_df)
candidate_count = filtered_df["candidate"].nunique()
constituency_count = filtered_df["constituency"].nunique()

candidate_votes = filtered_df["candidate"].value_counts()
leader = candidate_votes.index[0] if not candidate_votes.empty else "N/A"
leader_votes = candidate_votes.iloc[0] if not candidate_votes.empty else 0
leader_percentage = (leader_votes / total_votes * 100) if total_votes > 0 else 0

# -----------------------------
# Top metrics Cards
# -----------------------------
m_col1, m_col2, m_col3, m_col4 = st.columns(4)

with m_col1:
    st.markdown(f"""
        <div class="metric-card">
            <p class="metric-title">Total Votes</p>
            <p class="metric-value">{{total_votes:,}}</p>
        </div>
    """, unsafe_allow_html=True)

with m_col2:
    st.markdown(f"""
        <div class="metric-card">
            <p class="metric-title">Candidates</p>
            <p class="metric-value">{{candidate_count}}</p>
        </div>
    """, unsafe_allow_html=True)

with m_col3:
    st.markdown(f"""
        <div class="metric-card">
            <p class="metric-title">Constituencies</p>
            <p class="metric-value">{{constituency_count}}</p>
        </div>
    """, unsafe_allow_html=True)

with m_col4:
    leader_subtitle = f"{{leader_votes:,}} votes ({{leader_percentage:.1f}}%)" if leader != "N/A" else "No votes"
    st.markdown(f"""
        <div class="metric-card" style="border-left-color: #047857;">
            <p class="metric-title">Current Leader</p>
            <p class="metric-value" style="font-size: 1.6rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{{leader}}</p>
            <p class="metric-subtitle">{{leader_subtitle}}</p>
        </div>
    """, unsafe_allow_html=True)


# -----------------------------
# Dashboard Layout
# -----------------------------
row1_col1, row1_col2 = st.columns([3, 2])

# CANDIDATE PERFORMANCE
with row1_col1:
    st.markdown("<h3>Candidate Performance</h3>", unsafe_allow_html=True)
    # Use native Streamlit bar chart for clean, interactive visualization
    st.bar_chart(candidate_votes, color="#0ea5e9", height=350)

# CANDIDATE LEADERBOARD
with row1_col2:
    st.markdown("<h3>Leaderboard</h3>", unsafe_allow_html=True)

    leaderboard_df = pd.DataFrame({{
        "Candidate": candidate_votes.index,
        "Votes": candidate_votes.values,
        "Vote Share (%)": (candidate_votes.values / total_votes * 100).round(1)
    }})
    leaderboard_df.index = range(1, len(leaderboard_df) + 1)
    leaderboard_df.index.name = "Rank"

    st.dataframe(
        leaderboard_df.style.format({{"Votes": "{{:,}}", "Vote Share (%)": "{{:.1f}}%"}}),
        use_container_width=True,
        height=350
    )

st.markdown("<hr/>", unsafe_allow_html=True)

row2_col1, row2_col2 = st.columns([1, 1])

# VOTING ACTIVITY OVER TIME
with row2_col1:
    st.markdown("<h3>Voting Activity Over Time</h3>", unsafe_allow_html=True)

    time_span = filtered_df["vote_time"].max() - filtered_df["vote_time"].min()

    # Determine sensible time aggregation
    if time_span.total_seconds() < 120:
        freq = "S" # seconds
    elif time_span.total_seconds() < 3600:
        freq = "15S" # 15 seconds
    elif time_span.total_seconds() < 86400:
        freq = "1Min" # 1 minute
    else:
        freq = "1H" # 1 hour

    trend = (
        filtered_df.set_index("vote_time")
        .resample(freq)
        .size()
        .rename("Votes")
    )

    # Only show chart if there's enough variation, else show basic count
    if len(trend) > 1:
        st.line_chart(trend, color="#0369a1", height=300)
    else:
        st.info("Not enough temporal data to display trend chart.")

# CONSTITUENCY ANALYTICS
with row2_col2:
    st.markdown("<h3>Constituency Analysis</h3>", unsafe_allow_html=True)

    # Breakdown of candidates by constituency
    constituency_pivot = pd.crosstab(
        filtered_df["constituency"],
        filtered_df["candidate"]
    )

    # Sort constituencies by total votes
    constituency_pivot["Total"] = constituency_pivot.sum(axis=1)
    constituency_pivot = constituency_pivot.sort_values("Total", ascending=False).drop(columns=["Total"])

    st.dataframe(
        constituency_pivot,
        use_container_width=True,
        height=300
    )

st.markdown("<hr/>", unsafe_allow_html=True)

# LATEST EVENTS
st.markdown("<h3>Latest Voting Events</h3>", unsafe_allow_html=True)

latest_events = filtered_df.sort_values("vote_time", ascending=False).head(15).copy()

# Format time nicely
latest_events["vote_time"] = latest_events["vote_time"].dt.strftime("%Y-%m-%d %H:%M:%S")
latest_events.columns = ["Event ID", "Candidate", "Constituency", "Vote Time"]

st.dataframe(
    latest_events,
    use_container_width=True,
    hide_index=True
)

# -----------------------------
# System Information Footer
# -----------------------------
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown(
    """
    <div style='text-align: center; color: #94a3b8; font-size: 0.8rem; border-top: 1px solid #f1f5f9; padding-top: 20px;'>
        <strong>Data Source:</strong> PostgreSQL &nbsp; | &nbsp;
        <strong>Refresh Interval:</strong> 5 seconds &nbsp; | &nbsp;
        <strong>Application:</strong> Streamlit<br>
        CivicSense • Academic Mini-Project
    </div>
    """,
    unsafe_allow_html=True
)

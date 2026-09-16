"""
dashboard/app.py (v3)
Streamlit frontend for MetroFlow - two-role login, capacity-based crowd
map, two alert types, admin broadcast, traffic patterns, station
report, and NL query.

Run (backend must already be running on port 8000):
  streamlit run app.py
"""

import requests
import pandas as pd
import plotly.express as px
import streamlit as st

API_URL = "http://localhost:8000"
st.set_page_config(page_title="MetroFlow", layout="wide")

# ---------------------------------------------------------------------------
# Two-role login (User Management Module - lightweight, not full RBAC)
# ---------------------------------------------------------------------------
DEMO_USERS = {
    "admin": {"password": "admin123", "role": "admin"},
    "operator": {"password": "operator123", "role": "operator"},
}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.username = None

if not st.session_state.logged_in:
    st.title("MetroFlow login")
    st.caption("Demo credentials: admin/admin123 (full access) or operator/operator123 (view-only)")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Log in"):
        user = DEMO_USERS.get(username)
        if user and user["password"] == password:
            st.session_state.logged_in = True
            st.session_state.role = user["role"]
            st.session_state.username = username
            st.rerun()
        else:
            st.error("Invalid username or password.")
    st.stop()

# ---------------------------------------------------------------------------
# Main dashboard
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(f"**Logged in as:** {st.session_state.username}")
    st.markdown(f"**Role:** {st.session_state.role}")
    if st.button("Log out"):
        st.session_state.logged_in = False
        st.rerun()

st.title("MetroFlow")
st.caption("AI-powered crowd prediction, capacity-based alerts, and scheduling recommendations")

col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    hour = st.slider("Hour of day", 0, 23, 18)
with col2:
    is_weekend = st.checkbox("Weekend")
with col3:
    is_holiday = st.checkbox("Holiday")

try:
    resp = requests.get(f"{API_URL}/predict_all",
                         params={"hour": hour, "is_weekend": int(is_weekend), "is_holiday": int(is_holiday)},
                         timeout=5)
    resp.raise_for_status()
    data = resp.json()
except requests.exceptions.RequestException:
    st.error("Couldn't reach the MetroFlow backend. Run: `uvicorn main:app --reload --port 8000` from backend/.")
    st.stop()

df = pd.DataFrame(data)

# --- Admin broadcast box ---
if st.session_state.role == "admin":
    with st.expander("Admin: post emergency broadcast"):
        msg = st.text_input("Broadcast message")
        b1, b2 = st.columns(2)
        if b1.button("Post broadcast") and msg:
            requests.post(f"{API_URL}/broadcast", params={"message": msg, "role": "admin"})
            st.rerun()
        if b2.button("Clear broadcast"):
            requests.delete(f"{API_URL}/broadcast", params={"role": "admin"})
            st.rerun()

try:
    bcast = requests.get(f"{API_URL}/broadcast", timeout=5).json().get("message")
    if bcast:
        st.error(f"📢 EMERGENCY BROADCAST: {bcast}")
except requests.exceptions.RequestException:
    pass

# --- Two alert types ---
high_crowd = df[df["overcrowding_alert"] == True]["station"].tolist()
delayed = df[df["delay_alert"] == True]["station"].tolist()

a1, a2 = st.columns(2)
with a1:
    if high_crowd:
        st.warning(f"Overcrowding predicted at: {', '.join(high_crowd)}")
    else:
        st.success("No overcrowding predicted at this hour.")
with a2:
    if delayed:
        st.warning(f"Delay risk at: {', '.join(delayed)}")
    else:
        st.success("No significant delay risk predicted.")

# --- Summary stats ---
stat1, stat2, stat3, stat4 = st.columns(4)
stat1.metric("Stations monitored", len(df))
stat2.metric("Avg crowd %", f"{df['crowd_pct'].mean():.1f}%")
stat3.metric("High-crowd stations", len(high_crowd))
stat4.metric("Delay-risk stations", len(delayed))

# --- Crowd map ---
st.subheader("Station crowd map")
color_map = {"low": "green", "medium": "orange", "high": "red"}
fig = px.scatter_map(
    df, lat="lat", lon="lon", color="level", color_discrete_map=color_map,
    size="predicted_passenger_count", hover_name="station",
    hover_data={"crowd_pct": True, "lat": False, "lon": False, "level": False},
    center={"lat": df["lat"].mean(), "lon": df["lon"].mean()},
    zoom=10.5, height=450,
)
fig.update_layout(map_style="open-street-map", margin={"r": 0, "t": 0, "l": 0, "b": 0})
st.plotly_chart(fig, use_container_width=True)

# --- Station table ---
st.subheader("Recommendations")
st.dataframe(
    df[["station", "predicted_passenger_count", "crowd_pct", "level", "simulated_delay_min", "message"]].rename(
        columns={"predicted_passenger_count": "predicted passengers", "crowd_pct": "crowd %",
                 "level": "crowd level", "simulated_delay_min": "delay (min)", "message": "recommendation"}
    ),
    use_container_width=True, hide_index=True,
)

# --- Traffic pattern analysis ---
st.subheader("Traffic pattern analysis")
try:
    patterns = requests.get(f"{API_URL}/traffic_patterns", timeout=5).json()
    tp1, tp2 = st.columns(2)
    with tp1:
        by_hour_df = pd.DataFrame(list(patterns["by_hour"].items()), columns=["hour", "avg_passengers"]).sort_values("hour")
        st.line_chart(by_hour_df.set_index("hour"))
        st.caption("Average ridership by hour of day")
    with tp2:
        by_day_df = pd.DataFrame(list(patterns["by_day"].items()), columns=["day", "avg_passengers"])
        st.bar_chart(by_day_df.set_index("day"))
        st.caption("Average ridership by day of week")
except requests.exceptions.RequestException:
    st.info("Traffic pattern data unavailable.")

# --- Station performance report ---
st.subheader("Station performance report")
try:
    report = requests.get(f"{API_URL}/station_report", timeout=5).json()
    report_df = pd.DataFrame(report)
    st.dataframe(report_df, use_container_width=True, hide_index=True)
    st.download_button("Download report as CSV", report_df.to_csv(index=False), "station_report.csv")
except requests.exceptions.RequestException:
    st.info("Station report unavailable.")

# --- NL query ---
st.subheader("Ask about a station")
question = st.text_input('e.g. "how crowded will Grand Central be at 6pm?"', key="nl_query")
if question:
    try:
        q_resp = requests.get(f"{API_URL}/query", params={"text": question}, timeout=5)
        q_resp.raise_for_status()
        st.info(q_resp.json()["answer"])
    except requests.exceptions.RequestException:
        st.error("Couldn't reach the backend for this query.")

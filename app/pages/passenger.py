"""
passenger.py — Passenger Planner page.

Allows a passenger to:
  1. Select a route and travel time
  2. Enter conditions (weather, events)
  3. See predicted passenger count and crowd level
  4. See a simple explanation of the prediction
  5. See all 24 hours ranked by crowding (alternative times)
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from src.config import ROUTES, DEFAULT_VEHICLE_CAPACITY, CROWD_COLOURS
from src.prediction import (
    load_model, predict_demand, predict_hourly_profile,
    get_route_avg_demand, ModelNotFoundError,
)
from src.crowd_management import classify_crowd, compute_utilisation, get_crowd_colour
from src.data_processing import load_data


# ── Cached loaders ─────────────────────────────────────────────
@st.cache_resource(show_spinner="Loading model…")
def get_model_bundle():
    return load_model()

@st.cache_data(show_spinner="Loading dataset…")
def get_data():
    return load_data()


# ── Helpers ────────────────────────────────────────────────────
def crowd_badge(level: str) -> str:
    colour = CROWD_COLOURS.get(level, "#95a5a6")
    return f'<span style="background:{colour};color:white;padding:4px 12px;border-radius:12px;font-weight:bold">{level}</span>'


def render():
    st.title("🧍 Passenger Planner")
    st.markdown(
        "Enter your journey details below to see the **predicted crowd level** "
        "and find a less-busy travel time."
    )

    # ── Model / data availability checks ───────────────────────
    try:
        model_bundle = get_model_bundle()
    except ModelNotFoundError as e:
        st.error(f"⚠️ Model not found. {e}")
        st.info("Run `python src/train_model.py` to train the model first.")
        return

    try:
        df = get_data()
    except FileNotFoundError as e:
        st.error(f"⚠️ Dataset not found. {e}")
        return

    route_list = sorted(df["route"].unique().tolist())
    day_names  = ["Monday", "Tuesday", "Wednesday",
                   "Thursday", "Friday", "Saturday", "Sunday"]

    # ── Input form ─────────────────────────────────────────────
    st.subheader("Journey Details")
    col1, col2, col3 = st.columns(3)

    with col1:
        selected_route = st.selectbox("Route", route_list)
        selected_day   = st.selectbox("Day of Week", day_names)
        day_of_week    = day_names.index(selected_day)

    with col2:
        selected_hour = st.slider("Departure Hour", 0, 23, 8,
                                   format="%02d:00")
        temperature   = st.number_input("Temperature (°C)", -10.0, 45.0, 22.0, 0.5)

    with col3:
        is_raining   = st.checkbox("🌧 Raining?")
        nearby_event = st.checkbox("🎉 Nearby Event?")
        st.caption("Nearby events (concerts, sports) can significantly increase demand.")

    st.divider()

    # ── Derive supporting inputs ───────────────────────────────
    route_avg = get_route_avg_demand(selected_route, df)
    capacity  = ROUTES.get(selected_route, DEFAULT_VEHICLE_CAPACITY)

    # Simple heuristic for prev_passenger_count: use the average for previous hour
    prev_hour   = max(0, selected_hour - 1)
    prev_count  = predict_demand(
        route=selected_route, hour=prev_hour,
        day_of_week=day_of_week, temperature=temperature,
        is_raining=int(is_raining), nearby_event=int(nearby_event),
        prev_passenger_count=route_avg, route_avg_demand=route_avg,
        model_bundle=model_bundle,
    )

    # ── Main prediction ────────────────────────────────────────
    predicted = predict_demand(
        route=selected_route, hour=selected_hour,
        day_of_week=day_of_week, temperature=temperature,
        is_raining=int(is_raining), nearby_event=int(nearby_event),
        prev_passenger_count=prev_count, route_avg_demand=route_avg,
        model_bundle=model_bundle,
    )

    utilisation = compute_utilisation(predicted, route=selected_route, capacity=capacity)
    crowd_level = classify_crowd(utilisation)
    colour      = get_crowd_colour(crowd_level)

    # ── KPI cards ──────────────────────────────────────────────
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Predicted Passengers", f"{int(predicted)}", help="ML model prediction")
    k2.metric("Vehicle Capacity",     f"{capacity}")
    k3.metric("Utilisation",          f"{utilisation*100:.1f}%")
    k4.metric("Crowd Level",          crowd_level)

    # Colour-coded crowd badge
    st.markdown(
        f"### Crowd Level: {crowd_badge(crowd_level)}",
        unsafe_allow_html=True,
    )

    # ── Explanation ────────────────────────────────────────────
    explanations = {
        "Low": (
            "🟢 **Low crowding.** The vehicle is predicted to be comfortably below "
            "half-full. You should have plenty of space to sit."
        ),
        "Moderate": (
            "🟡 **Moderate crowding.** The vehicle is likely to be around half to "
            "three-quarters full. Seating may not be guaranteed, but standing space "
            "will be available."
        ),
        "High": (
            "🟠 **High crowding.** The vehicle is expected to be near its capacity. "
            "Consider travelling 30–60 minutes earlier or later for a more comfortable journey."
        ),
        "Critical": (
            "🔴 **Critical crowding.** The vehicle is predicted to be at or above capacity. "
            "Strong recommendation: avoid this service if possible. "
            "Try an alternative time shown in the chart below."
        ),
    }
    st.info(explanations[crowd_level])

    # ── Factor explanation ─────────────────────────────────────
    with st.expander("🔍 What influenced this prediction?"):
        factors = []
        is_peak = 7 <= selected_hour <= 9 or 17 <= selected_hour <= 19
        is_wknd = day_of_week >= 5

        if is_peak:
            factors.append("⬆️ **Peak hour** (7–9 AM or 5–7 PM) — typically highest demand")
        if is_wknd:
            factors.append("⬇️ **Weekend** — generally lower commuter demand on most routes")
        if nearby_event:
            factors.append("⬆️ **Nearby event** — can increase demand by up to 50%")
        if is_raining:
            factors.append("⬆️ **Rain** — slightly increases transit use (fewer cyclists/walkers)")
        if temperature < 10 or temperature > 32:
            factors.append("⬆️ **Extreme temperature** — encourages transit over walking")

        if not factors:
            factors.append("ℹ️ No strong demand spikes detected for these conditions.")

        for f in factors:
            st.markdown(f"- {f}")

    st.divider()

    # ── Full 24-hour profile chart ─────────────────────────────
    st.subheader("📈 24-Hour Demand Profile — Alternative Travel Times")
    st.caption("Hover over the bars to see predicted passenger counts for each hour.")

    with st.spinner("Generating daily profile…"):
        hourly = predict_hourly_profile(
            route=selected_route, day_of_week=day_of_week,
            temperature=temperature, is_raining=int(is_raining),
            nearby_event=int(nearby_event), route_avg_demand=route_avg,
            model_bundle=model_bundle,
        )

    hours_df = pd.DataFrame(hourly)
    hours_df["crowd_level"] = hours_df["utilisation"].apply(classify_crowd)
    hours_df["colour"]      = hours_df["crowd_level"].apply(get_crowd_colour)
    hours_df["hour_label"]  = hours_df["hour"].apply(lambda h: f"{h:02d}:00")

    fig = go.Figure()
    for level, colour_hex in CROWD_COLOURS.items():
        mask = hours_df["crowd_level"] == level
        if mask.any():
            subset = hours_df[mask]
            fig.add_trace(go.Bar(
                x=subset["hour_label"],
                y=subset["predicted_count"],
                name=level,
                marker_color=colour_hex,
                text=subset["predicted_count"].astype(int),
                textposition="outside",
                hovertemplate=(
                    "<b>%{x}</b><br>"
                    "Passengers: %{y}<br>"
                    f"Level: {level}<extra></extra>"
                ),
            ))

    # Mark selected hour
    selected_label = f"{selected_hour:02d}:00"
    fig.add_vline(
        x=selected_label, line_dash="dash", line_color="navy",
        annotation_text="Your time", annotation_position="top right",
    )
    fig.add_hline(
        y=capacity, line_dash="dot", line_color="red",
        annotation_text=f"Capacity ({capacity})", annotation_position="right",
    )

    fig.update_layout(
        barmode="stack",
        xaxis_title="Hour of Day",
        yaxis_title="Predicted Passengers",
        legend_title="Crowd Level",
        height=420,
        margin=dict(t=30, b=40),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Recommend better times ─────────────────────────────────
    better = [
        h for h in hourly
        if classify_crowd(h["utilisation"]) in ("Low", "Moderate")
        and h["hour"] != selected_hour
    ]
    if better:
        st.subheader("✅ Recommended Low-Crowd Travel Times")
        cols = st.columns(min(4, len(better[:8])))
        for i, slot in enumerate(better[:8]):
            lvl = classify_crowd(slot["utilisation"])
            cols[i % 4].metric(
                label=f"{slot['hour']:02d}:00",
                value=f"{int(slot['predicted_count'])} pax",
                delta=f"{lvl}",
            )
    elif crowd_level in ("Low", "Moderate"):
        st.success("Your selected time already has low crowding — great choice!")
    else:
        st.warning("No significantly quieter times found for this route/day/conditions.")


# Execute page
render()

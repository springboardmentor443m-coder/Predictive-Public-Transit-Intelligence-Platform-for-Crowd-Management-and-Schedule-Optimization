"""
operator.py — Operator Analytics Dashboard page.

Shows:
  - KPI summary cards
  - Passenger demand by hour (line chart)
  - Route comparison (bar chart)
  - Crowd-level distribution (pie chart)
  - Peak-hour analysis (heatmap)
  - Route utilisation (horizontal bar)
  - Schedule recommendations table
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from src.config import ROUTES, DEFAULT_VEHICLE_CAPACITY, CROWD_COLOURS
from src.data_processing import load_data, get_data_summary
from src.crowd_management import classify_dataframe, get_crowd_summary
from src.prediction import load_model, predict_hourly_profile, ModelNotFoundError, get_route_avg_demand
from src.schedule_optimizer import generate_daily_recommendations


@st.cache_data(show_spinner="Loading dataset…")
def get_df():
    return load_data()

@st.cache_resource(show_spinner="Loading model…")
def get_model():
    return load_model()


def render():
    st.title("📊 Operator Dashboard")
    st.markdown(
        "Analytics and schedule recommendations for transit operators. "
        "Data is synthetic and labelled as such in every row."
    )

    # ── Load data ──────────────────────────────────────────────
    try:
        df = get_df()
    except FileNotFoundError as e:
        st.error(f"⚠️ {e}")
        return

    df = classify_dataframe(df)

    # ── Filters sidebar ────────────────────────────────────────
    with st.sidebar:
        st.subheader("🔧 Filters")
        day_names = ["All Days", "Monday", "Tuesday", "Wednesday",
                     "Thursday", "Friday", "Saturday", "Sunday"]
        selected_day = st.selectbox("Filter by Day", day_names, key="op_day")
        if selected_day != "All Days":
            day_idx = day_names.index(selected_day) - 1
            df = df[df["day_of_week"] == day_idx]

        selected_routes = st.multiselect(
            "Filter by Route",
            sorted(df["route"].unique()),
            default=None,
            key="op_routes",
        )
        if selected_routes:
            df = df[df["route"].isin(selected_routes)]

    if df.empty:
        st.warning("No data matches the current filters.")
        return

    # ═══════════════════════════════════════════════════════════
    # Section 1 — KPI Cards
    # ═══════════════════════════════════════════════════════════
    st.subheader("📌 Key Performance Indicators")
    summary = get_data_summary(df)
    crowd_sum = get_crowd_summary(df)

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Total Routes",     summary["total_routes"])
    k2.metric("Total Records",    f"{summary['total_records']:,}")
    k3.metric("Avg Demand",       f"{summary['avg_demand']} pax")
    k4.metric("Peak Demand",      f"{summary['peak_demand']} pax")
    k5.metric("High/Critical %",  f"{summary['pct_high_critical']}%",
              delta_color="inverse")

    st.divider()

    # ═══════════════════════════════════════════════════════════
    # Section 2 — Demand by Hour  (line chart)
    # ═══════════════════════════════════════════════════════════
    st.subheader("📈 Average Passenger Demand by Hour of Day")
    hourly_avg = (
        df.groupby("hour")["passenger_count"]
        .agg(["mean", "std", "max"])
        .reset_index()
        .rename(columns={"mean": "avg", "std": "std_dev", "max": "peak"})
    )

    fig_hourly = go.Figure()
    fig_hourly.add_trace(go.Scatter(
        x=hourly_avg["hour"], y=hourly_avg["avg"],
        mode="lines+markers", name="Average", line=dict(color="#3498db", width=2.5),
        hovertemplate="Hour %{x}:00<br>Avg: %{y:.1f} pax<extra></extra>",
    ))
    fig_hourly.add_trace(go.Scatter(
        x=hourly_avg["hour"], y=hourly_avg["peak"],
        mode="lines", name="Peak", line=dict(color="#e74c3c", dash="dot", width=1.5),
        hovertemplate="Hour %{x}:00<br>Peak: %{y} pax<extra></extra>",
    ))
    # Shade AM peak
    fig_hourly.add_vrect(x0=7, x1=9, fillcolor="#3498db", opacity=0.08,
                          annotation_text="AM Peak", annotation_position="top left")
    fig_hourly.add_vrect(x0=17, x1=19, fillcolor="#e74c3c", opacity=0.08,
                          annotation_text="PM Peak", annotation_position="top left")
    fig_hourly.update_layout(
        xaxis_title="Hour of Day", yaxis_title="Passengers",
        height=380, margin=dict(t=20, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_hourly, use_container_width=True)

    # ═══════════════════════════════════════════════════════════
    # Section 3 — Route Comparison + Crowd Distribution (side by side)
    # ═══════════════════════════════════════════════════════════
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("🚌 Route Comparison")
        route_stats = (
            df.groupby("route")["passenger_count"]
            .agg(["mean", "max"])
            .reset_index()
            .rename(columns={"mean": "Avg Demand", "max": "Peak Demand"})
            .sort_values("Avg Demand", ascending=True)
        )
        # Short route labels
        route_stats["short_name"] = route_stats["route"].str.replace(r"Route \d+ - ", "", regex=True)

        fig_routes = go.Figure()
        fig_routes.add_trace(go.Bar(
            y=route_stats["short_name"], x=route_stats["Avg Demand"],
            orientation="h", name="Avg", marker_color="#3498db",
            hovertemplate="%{y}<br>Avg: %{x:.1f} pax<extra></extra>",
        ))
        fig_routes.add_trace(go.Bar(
            y=route_stats["short_name"], x=route_stats["Peak Demand"],
            orientation="h", name="Peak", marker_color="#e74c3c", opacity=0.5,
            hovertemplate="%{y}<br>Peak: %{x} pax<extra></extra>",
        ))
        fig_routes.update_layout(
            barmode="overlay", xaxis_title="Passengers",
            height=380, margin=dict(t=20, b=40),
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_routes, use_container_width=True)

    with col_right:
        st.subheader("🥧 Crowd Level Distribution")
        crowd_labels  = list(crowd_sum.keys())
        crowd_values  = [crowd_sum[k]["count"] for k in crowd_labels]
        crowd_colours = [crowd_sum[k]["colour"]  for k in crowd_labels]

        fig_pie = go.Figure(go.Pie(
            labels=crowd_labels, values=crowd_values,
            marker=dict(colors=crowd_colours),
            hole=0.4, textinfo="percent+label",
            hovertemplate="%{label}<br>Count: %{value}<br>%{percent}<extra></extra>",
        ))
        fig_pie.update_layout(
            height=380, margin=dict(t=20, b=20),
            showlegend=True, legend=dict(orientation="h", y=-0.1),
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    # ═══════════════════════════════════════════════════════════
    # Section 4 — Peak-hour Heatmap
    # ═══════════════════════════════════════════════════════════
    st.subheader("🌡️ Demand Heatmap — Route × Hour")
    heatmap_data = (
        df.groupby(["route", "hour"])["passenger_count"]
        .mean()
        .reset_index()
    )
    heatmap_pivot = heatmap_data.pivot(index="route", columns="hour", values="passenger_count")
    heatmap_pivot.index = heatmap_pivot.index.str.replace(r"Route \d+ - ", "", regex=True)

    fig_heat = px.imshow(
        heatmap_pivot,
        color_continuous_scale="RdYlGn_r",
        aspect="auto",
        labels=dict(x="Hour of Day", y="Route", color="Avg Passengers"),
        title="",
    )
    fig_heat.update_layout(height=420, margin=dict(t=10, b=40))
    st.plotly_chart(fig_heat, use_container_width=True)

    # ═══════════════════════════════════════════════════════════
    # Section 5 — Route Utilisation
    # ═══════════════════════════════════════════════════════════
    st.subheader("⚡ Route Utilisation")
    util_stats = (
        df.groupby("route")["utilisation"]
        .mean()
        .reset_index()
        .sort_values("utilisation", ascending=True)
    )
    util_stats["short_name"] = util_stats["route"].str.replace(r"Route \d+ - ", "", regex=True)
    util_stats["util_pct"]   = (util_stats["utilisation"] * 100).round(1)
    util_stats["colour"]     = util_stats["utilisation"].apply(
        lambda u: "#e74c3c" if u >= 0.90 else "#e67e22" if u >= 0.75
                  else "#f39c12" if u >= 0.50 else "#2ecc71"
    )

    fig_util = go.Figure(go.Bar(
        y=util_stats["short_name"],
        x=util_stats["util_pct"],
        orientation="h",
        marker_color=util_stats["colour"],
        text=util_stats["util_pct"].apply(lambda v: f"{v}%"),
        textposition="outside",
        hovertemplate="%{y}<br>Avg Utilisation: %{x:.1f}%<extra></extra>",
    ))
    fig_util.add_vline(x=75, line_dash="dash", line_color="#e67e22",
                       annotation_text="High threshold (75%)")
    fig_util.add_vline(x=90, line_dash="dash", line_color="#e74c3c",
                       annotation_text="Critical threshold (90%)")
    fig_util.update_layout(
        xaxis_title="Average Utilisation (%)", xaxis_range=[0, 120],
        height=380, margin=dict(t=10, b=40),
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_util, use_container_width=True)

    # ═══════════════════════════════════════════════════════════
    # Section 6 — Schedule Recommendations
    # ═══════════════════════════════════════════════════════════
    st.subheader("🗓️ Schedule Recommendations")
    st.caption("Based on predicted peak-hour demand across all routes.")

    try:
        model_bundle = get_model()
    except ModelNotFoundError:
        st.warning("Train the model first to see schedule recommendations.")
        return

    all_recs = []
    route_list = sorted(df["route"].unique().tolist())

    # Generate for the day filter; default weekday if "All Days" selected
    filter_day = 0  # Monday default
    if selected_day != "All Days":
        filter_day = day_names.index(selected_day) - 1

    with st.spinner("Computing recommendations for all routes…"):
        for route in route_list:
            capacity   = ROUTES.get(route, DEFAULT_VEHICLE_CAPACITY)
            route_avg  = get_route_avg_demand(route, df)
            hourly_profile = predict_hourly_profile(
                route=route, day_of_week=filter_day,
                temperature=20.0, is_raining=0, nearby_event=0,
                route_avg_demand=route_avg, model_bundle=model_bundle,
            )
            recs = generate_daily_recommendations(route, hourly_profile, capacity)
            all_recs.extend(recs)

    recs_df = pd.DataFrame(all_recs)
    recs_df = recs_df[recs_df["crowd_level"].isin(["High", "Critical"])].copy()
    recs_df = recs_df.sort_values(["priority", "route", "hour"])

    if recs_df.empty:
        st.success("✅ No High or Critical crowding predicted for the selected filters.")
    else:
        # Colour-coded rows
        def highlight_crowd(row):
            colours = {"Critical": "#fde8e8", "High": "#fef3e2"}
            bg = colours.get(row["crowd_level"], "")
            return [f"background-color: {bg}"] * len(row)

        display_df = recs_df[[
            "route", "hour_str", "passenger_count",
            "utilisation", "crowd_level", "action",
        ]].rename(columns={
            "route":           "Route",
            "hour_str":        "Hour",
            "passenger_count": "Pred. Passengers",
            "utilisation":     "Utilisation %",
            "crowd_level":     "Crowd Level",
            "action":          "Recommended Action",
        })

        st.dataframe(
            display_df.style.apply(highlight_crowd, axis=1),
            use_container_width=True,
            height=min(400, 40 + 35 * len(display_df)),
        )

        # Show reasoning for top 3 critical alerts
        critical_recs = recs_df[recs_df["crowd_level"] == "Critical"].head(3)
        if not critical_recs.empty:
            st.subheader("🔴 Critical Alerts — Detailed Reasoning")
            for _, row in critical_recs.iterrows():
                with st.expander(f"⚠️  {row['route']}  |  {row['hour_str']}  |  {row['utilisation']}% full"):
                    st.write(row["reason"])


render()

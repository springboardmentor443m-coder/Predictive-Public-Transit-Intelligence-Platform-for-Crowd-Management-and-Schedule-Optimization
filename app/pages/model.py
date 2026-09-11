"""
model.py — Model Analytics page.

Shows:
  - Which model was selected and why
  - MAE, RMSE, R² metrics for all three models
  - Feature importance bar chart
  - Predicted vs Actual scatter plot
  - Residual distribution histogram
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

from src.prediction import load_metadata, load_model, ModelNotFoundError
from src.config import FEATURE_COLUMNS


@st.cache_data(show_spinner="Loading model metadata…")
def get_metadata():
    return load_metadata()

@st.cache_resource(show_spinner="Loading model…")
def get_model_bundle():
    return load_model()


def render():
    st.title("🤖 Model Analytics")
    st.markdown(
        "Transparency into the machine-learning model: how it was trained, "
        "how accurate it is, and which features matter most."
    )

    # ── Load metadata ──────────────────────────────────────────
    meta = get_metadata()
    if not meta:
        st.error("⚠️ No model metadata found.")
        st.info("Run `python src/train_model.py` to train the model first.")
        return

    # ── Model Info Banner ──────────────────────────────────────
    best_name    = meta.get("best_model", "Unknown")
    best_metrics = meta.get("best_metrics", {})
    all_metrics  = meta.get("metrics", {})
    feat_imp     = meta.get("feature_importance", {})

    st.success(
        f"**Selected Model:** {best_name}  |  "
        f"Chosen because it achieved the **lowest RMSE** on the held-out test set."
    )

    # ── Key Metric Cards ───────────────────────────────────────
    st.subheader("📌 Best Model Performance (Test Set — 20% held out)")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Model",   best_name)
    m2.metric("MAE",     f"{best_metrics.get('MAE', 'N/A')} passengers",
              help="Mean Absolute Error — average size of prediction error")
    m3.metric("RMSE",    f"{best_metrics.get('RMSE', 'N/A')} passengers",
              help="Root Mean Squared Error — penalises large errors more")
    m4.metric("R²",      f"{best_metrics.get('R2', 'N/A')}",
              help="Proportion of variance explained (1.0 = perfect)")

    # ── R² interpretation ─────────────────────────────────────
    r2 = best_metrics.get("R2", 0)
    if r2 >= 0.90:
        st.info(f"📊 **R² = {r2}** — The model explains {r2*100:.1f}% of variance in passenger demand. This is strong performance on a structured synthetic dataset.")
    elif r2 >= 0.75:
        st.info(f"📊 **R² = {r2}** — The model explains {r2*100:.1f}% of variance. Good performance; real-world data would introduce more noise.")
    else:
        st.warning(f"📊 **R² = {r2}** — The model explains {r2*100:.1f}% of variance. Consider more features or hyperparameter tuning.")

    st.divider()

    # ═══════════════════════════════════════════════════════════
    # Model Comparison Table
    # ═══════════════════════════════════════════════════════════
    st.subheader("📋 Model Comparison — All Three Models")
    st.caption("Lower MAE and RMSE = better. Higher R² = better.")

    rows = []
    for name, metrics in all_metrics.items():
        rows.append({
            "Model":          name,
            "MAE ↓":          metrics.get("MAE"),
            "RMSE ↓":         metrics.get("RMSE"),
            "R² ↑":           metrics.get("R2"),
            "Train Time (s)": metrics.get("train_time_s"),
            "Selected":       "✅" if name == best_name else "",
        })
    comp_df = pd.DataFrame(rows).set_index("Model")

    def highlight_best(row):
        return ["background-color: #e8f5e9; font-weight: bold"
                if row.name == best_name else "" for _ in row]

    st.dataframe(
        comp_df.style.apply(highlight_best, axis=1).format({
            "MAE ↓":  "{:.3f}",
            "RMSE ↓": "{:.3f}",
            "R² ↑":   "{:.4f}",
        }),
        use_container_width=True,
    )

    with st.expander("ℹ️ What do these metrics mean?"):
        st.markdown("""
| Metric | Meaning | Ideal |
|--------|---------|-------|
| **MAE** | On average, predictions are off by this many passengers | As low as possible |
| **RMSE** | Like MAE but penalises large errors more heavily | As low as possible |
| **R²** | What fraction of demand variation the model explains | Close to 1.0 |

**Why Gradient Boosting?**
Gradient Boosting builds trees sequentially — each tree corrects the errors of the previous one.
This allows it to capture complex, non-linear relationships (e.g. the interaction between
peak hour + event + rain) that Linear Regression cannot.
        """)

    st.divider()

    # ═══════════════════════════════════════════════════════════
    # Feature Importance
    # ═══════════════════════════════════════════════════════════
    st.subheader("🔑 Feature Importance")
    if feat_imp:
        fi_df = (
            pd.DataFrame(list(feat_imp.items()), columns=["Feature", "Importance"])
            .sort_values("Importance", ascending=True)
        )
        # Human-readable feature names
        rename_map = {
            "route_encoded":        "Route (encoded)",
            "hour":                 "Hour of Day",
            "day_of_week":          "Day of Week",
            "is_weekend":           "Is Weekend",
            "is_peak_hour":         "Is Peak Hour",
            "temperature":          "Temperature (°C)",
            "is_raining":           "Is Raining",
            "nearby_event":         "Nearby Event",
            "prev_passenger_count": "Previous Hour Demand",
            "route_avg_demand":     "Route Avg Demand",
        }
        fi_df["Feature"] = fi_df["Feature"].map(rename_map).fillna(fi_df["Feature"])

        fig_fi = px.bar(
            fi_df, x="Importance", y="Feature", orientation="h",
            color="Importance",
            color_continuous_scale=["#2ecc71", "#f39c12", "#e74c3c"],
            labels={"Importance": "Relative Importance"},
            text=fi_df["Importance"].apply(lambda v: f"{v:.3f}"),
        )
        fig_fi.update_traces(textposition="outside")
        fig_fi.update_layout(
            height=420, margin=dict(t=10, b=40),
            coloraxis_showscale=False,
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_fi, use_container_width=True)

        # Top-3 narrative
        top3 = fi_df.sort_values("Importance", ascending=False).head(3)
        with st.expander("📖 Feature Importance — Plain English"):
            st.markdown(f"""
The three most important factors the model uses to predict passenger demand are:

1. **{top3.iloc[0]['Feature']}** — importance {top3.iloc[0]['Importance']:.3f}
2. **{top3.iloc[1]['Feature']}** — importance {top3.iloc[1]['Importance']:.3f}
3. **{top3.iloc[2]['Feature']}** — importance {top3.iloc[2]['Importance']:.3f}

*Importance* is measured as the fraction of total information gain across all
decision trees in the Gradient Boosting ensemble. A higher value means the model
relies more heavily on that feature when making predictions.
            """)
    else:
        st.info("Feature importance not available for the current model.")

    st.divider()

    # ═══════════════════════════════════════════════════════════
    # Predicted vs Actual Scatter
    # ═══════════════════════════════════════════════════════════
    st.subheader("🎯 Predicted vs Actual Passenger Count")
    st.caption("Points along the diagonal line indicate perfect predictions. Scatter shows prediction error.")

    y_test = meta.get("y_test_sample", [])
    y_pred = meta.get("y_pred_sample", [])

    if y_test and y_pred:
        pva_df = pd.DataFrame({
            "Actual":    [round(v, 1) for v in y_test],
            "Predicted": [round(v, 1) for v in y_pred],
        })
        pva_df["Error"] = (pva_df["Predicted"] - pva_df["Actual"]).abs()

        fig_scatter = px.scatter(
            pva_df, x="Actual", y="Predicted",
            color="Error",
            color_continuous_scale="RdYlGn_r",
            labels={"Error": "|Error| (pax)"},
            opacity=0.65,
            hover_data={"Actual": True, "Predicted": True, "Error": ":.1f"},
        )
        # Perfect-prediction diagonal
        max_val = max(pva_df["Actual"].max(), pva_df["Predicted"].max()) + 5
        fig_scatter.add_trace(go.Scatter(
            x=[0, max_val], y=[0, max_val],
            mode="lines", name="Perfect Prediction",
            line=dict(color="navy", dash="dash", width=1.5),
            showlegend=True,
        ))
        fig_scatter.update_layout(
            height=440, margin=dict(t=10, b=40),
            xaxis_title="Actual Passengers",
            yaxis_title="Predicted Passengers",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

        # ── Residual histogram ─────────────────────────────────
        st.subheader("📉 Residual Distribution")
        st.caption("Residual = Predicted − Actual. A good model has residuals centred near 0.")
        pva_df["Residual"] = pva_df["Predicted"] - pva_df["Actual"]

        fig_resid = px.histogram(
            pva_df, x="Residual", nbins=40,
            color_discrete_sequence=["#3498db"],
            labels={"Residual": "Residual (Predicted − Actual)"},
        )
        fig_resid.add_vline(x=0, line_dash="dash", line_color="red",
                            annotation_text="Zero error")
        fig_resid.update_layout(
            height=320, margin=dict(t=10, b=40),
            plot_bgcolor="rgba(0,0,0,0)",
            bargap=0.05,
        )
        st.plotly_chart(fig_resid, use_container_width=True)

    else:
        st.info("Prediction sample not available in metadata. Re-run `python src/train_model.py`.")

    # ── Training details ───────────────────────────────────────
    with st.expander("🛠️ Training Configuration"):
        st.markdown(f"""
| Setting | Value |
|---------|-------|
| Train / Test Split | {int((1-meta.get('test_size',0.2))*100)}% / {int(meta.get('test_size',0.2)*100)}% |
| Training rows | {meta.get('train_rows', 'N/A'):,} |
| Test rows | {meta.get('test_rows', 'N/A'):,} |
| Features | {len(meta.get('features', []))} |
| Random seed | 42 |
| Best model | {best_name} |
        """)


render()

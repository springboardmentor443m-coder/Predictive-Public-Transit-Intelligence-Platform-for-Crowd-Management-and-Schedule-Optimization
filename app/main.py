"""
main.py — Streamlit application entry point.

Defines the multi-page navigation sidebar and shared app configuration.

Run:
  streamlit run app/main.py
"""

import sys
from pathlib import Path

# Ensure src/ is importable when running from the app/ directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

# ── Page configuration (must be first Streamlit call) ─────────
st.set_page_config(
    page_title="Transit Intelligence Platform",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Navigation ─────────────────────────────────────────────────
PAGES = {
    "🧍 Passenger Planner":    "app/pages/passenger.py",
    "📊 Operator Dashboard":   "app/pages/operator.py",
    "🤖 Model Analytics":      "app/pages/model.py",
}

def main():
    # Sidebar branding
    with st.sidebar:
        st.image("https://img.icons8.com/fluency/96/bus.png", width=64)
        st.title("Transit Intelligence")
        st.caption("Crowd Management & Schedule Optimisation")
        st.divider()

        page = st.radio(
            "Navigate to",
            list(PAGES.keys()),
            label_visibility="collapsed",
        )
        st.divider()
        st.caption("📦 Data: Synthetic (GTFS-compatible structure)")
        st.caption("🤖 Model: Gradient Boosting Regressor")
        st.caption("v1.0  |  pratham-p branch")

    # Load the selected page
    selected_module = PAGES[page]
    page_path = PROJECT_ROOT / selected_module

    # Execute the page file in a safe namespace
    with open(page_path) as f:
        exec(compile(f.read(), str(page_path), "exec"), {"__name__": "__main__"})


if __name__ == "__main__":
    main()

"""
Observation Dashboard — Alpha Generator v3
Entry point: streamlit run observation/app.py
"""
import sys
from pathlib import Path

# Allow imports from project root
ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

st.set_page_config(
    page_title="Alpha Generator — Observer",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Alpha Generator — Observation Dashboard")
st.markdown(
    "Use the sidebar to navigate between pages. "
    "This dashboard is **read-only** — DeerFlow runs autonomously on the GCP VM."
)

col1, col2, col3 = st.columns(3)

try:
    from observation.utils.db import get_research_status, get_simulations, get_gold_alphas

    status = get_research_status()
    sims   = get_simulations()
    golds  = get_gold_alphas()

    with col1:
        st.metric("Agent Status", status.get("status", "unknown").upper())
    with col2:
        st.metric("Gold Alphas", len(golds) if not golds.empty else 0)
    with col3:
        st.metric("Total Simulations", len(sims) if not sims.empty else 0)

    agent_state = status.get("agent_state", "stopped")
    color = "green" if agent_state == "running" else "orange"
    st.markdown(f"**Agent:** :{color}[{agent_state}]  |  "
                f"Cycle: **{status.get('current_cycle', 0)}**  |  "
                f"Task: *{status.get('current_task', '—')}*")
except Exception as e:
    st.warning(f"Could not load status: {e}")

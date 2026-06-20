"""Page 1: Observatory — DeerFlow live status and research cycle log."""
import sys
from pathlib import Path
ROOT = Path(__file__).parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
from observation.utils.db import get_research_status, get_simulations

st.set_page_config(page_title="Observatory", page_icon="🔬", layout="wide")
st.title("Observatory")
st.caption("Real-time view of DeerFlow research activity")

status = get_research_status()

# ── Status Banner ─────────────────────────────────────────────────────────────
agent_state = status.get("agent_state", "stopped")
color = "green" if agent_state == "running" else ("orange" if agent_state == "idle" else "red")
st.markdown(f"### Agent: :{color}[{agent_state.upper()}]")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Cycle", status.get("current_cycle", 0))
c2.metric("Current Task", status.get("current_task", "—"))
c3.metric("Last Updated", status.get("last_updated", "—"))
c4.metric("Status", status.get("status", "idle"))

st.divider()

# ── Recent Simulations ────────────────────────────────────────────────────────
st.subheader("Recent Simulations")
sims = get_simulations()
if sims.empty:
    st.info("No simulations yet. DeerFlow will populate this once research begins.")
else:
    show_cols = [c for c in ["ts", "status", "sharpe", "fitness", "turnover", "formula"] if c in sims.columns]
    st.dataframe(sims[show_cols].head(50), use_container_width=True)

st.divider()

# ── Refresh ───────────────────────────────────────────────────────────────────
if st.button("Refresh"):
    st.rerun()

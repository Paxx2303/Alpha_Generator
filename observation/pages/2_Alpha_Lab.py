"""Page 2: Alpha Lab — all alphas with metrics, filters, family grouping."""
import sys
from pathlib import Path
ROOT = Path(__file__).parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import streamlit as st
from observation.utils.db import get_gold_alphas, get_simulations

st.set_page_config(page_title="Alpha Lab", page_icon="🎯", layout="wide")
st.title("Alpha Lab")
st.caption("All simulated alphas — filter, sort, and explore by signal family")

# ── Gold Alphas ───────────────────────────────────────────────────────────────
st.subheader("Gold Alphas (IQC Pass)")
gold = get_gold_alphas()
if gold.empty:
    st.info("No gold alphas in the database yet.")
else:
    # Sidebar filters
    with st.sidebar:
        st.header("Filters")
        min_sharpe = st.slider("Min Sharpe", 0.0, 3.0, 1.25, 0.05)
        min_fitness = st.slider("Min Fitness", 0.0, 3.0, 1.0, 0.05)

    filtered = gold.copy()
    if "sharpe" in filtered.columns:
        filtered = filtered[filtered["sharpe"] >= min_sharpe]
    if "fitness" in filtered.columns:
        filtered = filtered[filtered["fitness"] >= min_fitness]

    display_cols = [c for c in [
        "name", "sharpe", "fitness", "turnover_pct", "returns",
        "drawdown", "status", "settings"
    ] if c in filtered.columns]

    st.metric("Showing", len(filtered))
    st.dataframe(
        filtered[display_cols].sort_values("sharpe", ascending=False),
        use_container_width=True,
    )

    # Formula detail on row click
    st.divider()
    st.subheader("Formula Detail")
    if "name" in gold.columns:
        selected = st.selectbox("Select alpha", gold["name"].tolist())
        row = gold[gold["name"] == selected].iloc[0]
        col1, col2 = st.columns([1, 2])
        with col1:
            st.metric("Sharpe", f"{row.get('sharpe','?'):.2f}")
            st.metric("Fitness", f"{row.get('fitness','?'):.2f}")
            st.metric("Turnover", f"{row.get('turnover_pct', row.get('turnover', 0)):.1f}%")
            st.write("**Settings:**", row.get("settings", "—"))
            st.write("**Status:**", row.get("status", "—"))
        with col2:
            st.code(row.get("formula", "—"), language="javascript")

st.divider()

# ── All Simulations ───────────────────────────────────────────────────────────
st.subheader("All Simulations")
sims = get_simulations()
if sims.empty:
    st.info("No simulation history yet.")
else:
    show = [c for c in ["ts", "status", "sharpe", "fitness", "turnover", "settings"] if c in sims.columns]
    st.dataframe(sims[show].head(200), use_container_width=True)

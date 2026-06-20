"""Page 4: Knowledge Map — ChromaDB stats and semantic search."""
import sys
from pathlib import Path
ROOT = Path(__file__).parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
from observation.utils.db import get_document_stats

st.set_page_config(page_title="Knowledge Map", page_icon="🧠", layout="wide")
st.title("Knowledge Map")
st.caption("What DeerFlow knows — semantic knowledge base stats and search")

# ── ChromaDB stats ────────────────────────────────────────────────────────────
st.subheader("Knowledge Base Size")
st.info("ChromaDB lives on the VM (alpha-vm). Stats are only available when running locally or via VM dashboard.")
stats = {}

# SQLite doc stats as fallback
doc_stats = get_document_stats()
if doc_stats:
    st.metric("Legacy Chunks (SQLite)", doc_stats.get("total_chunks", 0))
    cats = doc_stats.get("by_category", [])
    if cats:
        import pandas as pd
        st.dataframe(pd.DataFrame(cats), use_container_width=True)

st.divider()

# ── Semantic Search ───────────────────────────────────────────────────────────
st.subheader("Semantic Search")
query = st.text_input("Search the knowledge base", placeholder="earnings reversal momentum...")
top_k = st.slider("Results", 1, 10, 5)

if query:
    st.warning("Semantic search requires ChromaDB on the VM. Not available in Cloud Run dashboard.")

st.divider()

# ── WQB Field Browser ─────────────────────────────────────────────────────────
st.subheader("WQB Field Browser (SQLite)")
from observation.utils.db import get_operator_list
ops = get_operator_list()
if ops.empty:
    st.info("No operator data in SQLite. Run a WQB metadata crawl first.")
else:
    cats = ["All"] + sorted(ops["category"].unique().tolist())
    cat_filter = st.selectbox("Category", cats)
    display = ops if cat_filter == "All" else ops[ops["category"] == cat_filter]
    st.dataframe(display, use_container_width=True)

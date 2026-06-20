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
try:
    from core.knowledge.vector_store import VectorStore
    vs = VectorStore()
    stats = vs.stats()
    c1, c2 = st.columns(2)
    c1.metric("Alpha Knowledge Chunks", stats.get("alpha_knowledge", 0))
    c2.metric("WQB Field Facts", stats.get("wqb_fields", 0))
except Exception as e:
    st.warning(f"ChromaDB not available: {e}")
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
    try:
        from core.knowledge.vector_store import VectorStore
        vs = VectorStore()
        results = vs.search(query, top_k=top_k)
        if not results:
            st.info("No results found. The knowledge base may be empty.")
        for i, r in enumerate(results, 1):
            meta = r.get("metadata", {})
            score = r.get("score", 0)
            with st.expander(
                f"**[{i}]** score={score:.3f}  "
                f"*{meta.get('source_type','?')} / {meta.get('category','?')}*"
            ):
                st.write(r.get("content", ""))
                if meta.get("source_id"):
                    st.caption(f"Source ID: {meta['source_id']}")
    except Exception as e:
        st.error(f"Search error: {e}")

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

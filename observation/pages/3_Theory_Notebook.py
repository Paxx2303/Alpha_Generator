"""Page 3: Theory Notebook — human-readable theories learned by the AI researcher."""
import sys
from pathlib import Path
ROOT = Path(__file__).parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
from observation.utils.db import get_theory_log, append_theory

st.set_page_config(page_title="Theory Notebook", page_icon="📓", layout="wide")
st.title("Theory Notebook")
st.caption(
    "Theories discovered by DeerFlow — written in plain language so you can learn "
    "quantitative research alongside the AI."
)

theories = get_theory_log()

if not theories:
    st.info("No theories recorded yet. DeerFlow will populate this after the first research cycle.")
else:
    # Sidebar filters
    with st.sidebar:
        st.header("Filter")
        all_tags = sorted({t for th in theories for t in th.get("tags", [])})
        selected_tags = st.multiselect("Tags", all_tags)
        min_confidence = st.slider("Min Confidence", 0.0, 1.0, 0.0, 0.05)

    filtered = [
        th for th in theories
        if th.get("confidence", 0) >= min_confidence
        and (not selected_tags or any(t in th.get("tags", []) for t in selected_tags))
    ]

    st.metric("Theories", len(filtered))

    # Sort by confidence descending
    filtered.sort(key=lambda x: x.get("confidence", 0), reverse=True)

    for th in filtered:
        conf = th.get("confidence", 0)
        conf_color = "green" if conf >= 0.7 else ("orange" if conf >= 0.4 else "red")
        tags = " ".join(f"`{t}`" for t in th.get("tags", []))

        with st.expander(f"**{th.get('title', 'Untitled')}**  — confidence: :{conf_color}[{conf:.0%}]"):
            st.write(th.get("body", ""))
            if th.get("source_url"):
                st.markdown(f"**Source:** {th['source_url']}")
            if tags:
                st.markdown(f"**Tags:** {tags}")
            st.caption(f"Recorded: {th.get('created_at', '?')[:10]}  |  ID: {th.get('id', '?')}")

st.divider()

# ── Add manual theory ─────────────────────────────────────────────────────────
with st.expander("Add your own theory"):
    t_title = st.text_input("Title")
    t_body  = st.text_area("Explanation (plain language)")
    t_conf  = st.slider("Confidence", 0.0, 1.0, 0.5, 0.05)
    t_src   = st.text_input("Source URL (optional)")
    t_tags  = st.text_input("Tags (comma-separated)")
    if st.button("Save Theory"):
        if t_title and t_body:
            append_theory({
                "title": t_title,
                "body": t_body,
                "confidence": t_conf,
                "source_url": t_src,
                "tags": [t.strip() for t in t_tags.split(",") if t.strip()],
            })
            st.success("Theory saved!")
            st.rerun()
        else:
            st.warning("Title and explanation are required.")

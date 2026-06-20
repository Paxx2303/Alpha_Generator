"""Page 5: Source Intel — knowledge source effectiveness analysis."""
import sys
from pathlib import Path
ROOT = Path(__file__).parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Source Intel", page_icon="📡", layout="wide")
st.title("Source Intel")
st.caption(
    "Which knowledge sources generate gold alphas? "
    "DeerFlow uses this to focus research on high-value sources."
)


def _load_store():
    from storage.store import Store
    return Store()


# ── Section A: Domain Overview ────────────────────────────────────────────────
st.subheader("A. Domain Overview (General vs WQB-Specific)")
try:
    s = _load_store()
    domain_stats = s.source_domain_stats()
    s.close()

    if not domain_stats:
        st.info("No source data yet. DeerFlow will populate this during research.")
    else:
        df_domain = pd.DataFrame(domain_stats)
        c1, c2 = st.columns(2)
        for _, row in df_domain.iterrows():
            col = c1 if row["source_domain"] == "general_quant" else c2
            col.metric(
                row["source_domain"],
                f"{row.get('effectiveness_pct', 0):.1f}% effective",
                f"{row.get('total_gold', 0)} gold / {row.get('total_tested', 0)} tested",
            )
        if len(df_domain) > 1:
            import plotly.express as px
            fig = px.bar(
                df_domain,
                x="source_domain",
                y="effectiveness_pct",
                color="source_domain",
                title="Effectiveness by Domain",
                labels={"effectiveness_pct": "Effectiveness %"},
            )
            st.plotly_chart(fig, use_container_width=True)
except Exception as e:
    st.error(f"Could not load domain stats: {e}")

st.divider()

# ── Section B: By Source Type ─────────────────────────────────────────────────
st.subheader("B. By Source Type")
try:
    s = _load_store()
    type_stats = s.source_type_stats()
    s.close()

    if type_stats:
        df_type = pd.DataFrame(type_stats)
        st.dataframe(
            df_type.sort_values("effectiveness_pct", ascending=False),
            use_container_width=True,
        )
    else:
        st.info("No type-level data yet.")
except Exception as e:
    st.error(f"Could not load type stats: {e}")

st.divider()

# ── Section C: Individual Sources ─────────────────────────────────────────────
st.subheader("C. Individual Sources")
try:
    s = _load_store()
    all_sources = s.all_sources(include_blacklisted=False)
    s.close()

    if not all_sources:
        st.info("No sources registered yet.")
    else:
        df = pd.DataFrame(all_sources)

        with st.sidebar:
            st.header("Filter Sources")
            domain_filter = st.selectbox("Domain", ["All"] + sorted(df["source_domain"].unique().tolist()))
            type_filter   = st.selectbox("Type",   ["All"] + sorted(df["source_type"].unique().tolist()))

        filtered = df.copy()
        if domain_filter != "All":
            filtered = filtered[filtered["source_domain"] == domain_filter]
        if type_filter != "All":
            filtered = filtered[filtered["source_type"] == type_filter]

        display_cols = [c for c in [
            "title", "source_domain", "source_type",
            "alphas_tested", "alphas_gold", "last_checked", "url"
        ] if c in filtered.columns]

        st.metric("Sources", len(filtered))
        st.dataframe(filtered[display_cols], use_container_width=True)

        st.divider()
        st.subheader("Blacklist Source")
        source_ids = filtered["id"].tolist() if "id" in filtered.columns else []
        if source_ids:
            to_blacklist = st.selectbox("Source ID", source_ids)
            reason = st.text_input("Reason")
            if st.button("Blacklist") and reason:
                s = _load_store()
                s.blacklist_source(to_blacklist, reason)
                s.close()
                st.success(f"Source {to_blacklist} blacklisted.")
                st.rerun()
except Exception as e:
    st.error(f"Could not load sources: {e}")

st.divider()

# ── Section D: Revisit Queue ──────────────────────────────────────────────────
st.subheader("D. Crawl Queue — Sources Ready to Revisit")
try:
    from core.knowledge.source_registry import SourceRegistry
    reg = SourceRegistry()
    all_src = _load_store().all_sources()
    revisit = [r for r in all_src if reg.should_revisit(r["id"])]
    if not revisit:
        st.info("No sources flagged for revisit.")
    else:
        st.dataframe(pd.DataFrame(revisit)[["id", "title", "source_type", "last_checked"]])
        st.caption("Tell DeerFlow to prioritize these in the next research cycle by setting them in the Planner config.")
except Exception as e:
    st.warning(f"Could not compute revisit queue: {e}")

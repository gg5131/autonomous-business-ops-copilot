"""Benchmarks page placeholder representing Phase 7 specifications."""

from __future__ import annotations

import streamlit as st
from frontend.utils.state_helpers import init_session_state, get_current_role, inject_custom_css

st.set_page_config(page_title="Benchmarks", page_icon="📈", layout="wide")
init_session_state()
inject_custom_css()

if not st.session_state.get("user_logged_in", False):
    st.warning("⚠️ Access Denied: Please log in at the main page first.")
    st.stop()

st.title("📈 Benchmarks Dashboard")
st.markdown(f"Active Role Session: **{get_current_role()}**")


st.markdown("---")

st.info("📈 **Benchmarks Dashboard Placeholder**\nThis module will be completed in **Phase 7 (Evaluation & Benchmarks)**. It will support running synthetic ticket generations and generating 5-way comparative reports between manual, single-LLM, vector-RAG, and GraphRAG pipelines.")

st.markdown("""
### Planned Features:
- **Baseline Comparators**: Side-by-side performance benchmarks.
- **RAGAS / DeepEval Logs**: Groundedness, precision, recall, and cost analytics charts.
- **Reports Export**: Markdown and PDF summary downloads.
""")

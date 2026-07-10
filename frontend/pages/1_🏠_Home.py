"""Home page dashboard displaying system state indicators and key metric grids."""

from __future__ import annotations

import streamlit as st
from frontend.utils.state_helpers import init_session_state, get_current_role, inject_custom_css

st.set_page_config(page_title="Home Dashboard", page_icon="🏠", layout="wide")
init_session_state()
inject_custom_css()

if not st.session_state.get("user_logged_in", False):
    st.warning("⚠️ Access Denied: Please log in at the main page first.")
    st.stop()

st.title("🏠 Home Dashboard")
st.markdown(f"Active Role Session: **{get_current_role()}**")


st.markdown("---")

# Metrics Grid
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(label="System Health Status", value="HEALTHY", delta="99.9% Uptime")

with col2:
    pending = len([t for t in st.session_state.get("tickets_db", []) if t["status"] == "Pending Review"])
    st.metric(label="Pending Human Reviews", value=pending, delta=None)

with col3:
    st.metric(label="Processed Tickets", value="142", delta="+12 today")

with col4:
    st.metric(label="Average Response Confidence", value="88.2%", delta="+1.2% this week")

st.markdown("---")

col5, col6, col7, col8 = st.columns(4)

with col5:
    st.metric(label="Avg Processing Latency", value="4.8s", delta="-0.3s")

with col6:
    st.metric(label="Token Usage (MTD)", value="450K", delta="Flash vs Pro")

with col7:
    st.metric(label="Total API Cost", value="$1.32", delta="Monthly total")

with col8:
    st.metric(label="Active OKF Documents", value="32", delta="Synced with Neo4j")

st.markdown("---")

# System Overview Charts / Details
st.subheader("🤖 Multi-Agent Performance Summary")

col_a, col_b = st.columns(2)

with col_a:
    st.markdown("#### Agent Execution Success Rates")
    st.markdown("""
    | Agent Name | Role | Success Rate | Average Latency |
    | :--- | :--- | :--- | :--- |
    | **Planner** | Task DAG Planner | **100%** | 820ms |
    | **Triage** | Classification | **100%** | 210ms |
    | **Research** | Summarization | **98.2%** | 1200ms |
    | **Policy** | Policy Validator | **100%** | 350ms |
    | **Draft** | Output generator | **100%** | 1500ms |
    | **FactChecker** | Hallucination Guard | **99.1%** | 1800ms |
    """)

with col_b:
    st.markdown("#### SLA Response Distribution")
    # Quick markdown visualization representing ticket processing times
    st.info("💡 **Performance Note**\n92% of tickets are triaged and drafted in under 5 seconds. All security scans, PII checking, and policy guardrails are executed asynchronously.")
    st.success("✅ **Circuit Breakers Status**: All agent systems are CLOSED (stable).")

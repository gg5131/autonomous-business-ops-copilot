"""Agent Inspector page visualizing execution DAGs, timeline Gantt, and prompt variables."""

from __future__ import annotations

import streamlit as st
import time
from frontend.utils.state_helpers import init_session_state, get_current_role, inject_custom_css

st.set_page_config(page_title="Agent Execution Inspector", page_icon="🔍", layout="wide")
init_session_state()
inject_custom_css()

if not st.session_state.get("user_logged_in", False):
    st.warning("⚠️ Access Denied: Please log in at the main page first.")
    st.stop()

st.title("🔍 Agent Execution Inspector")
st.markdown(f"Active Role Session: **{get_current_role()}**")


st.markdown("---")

# Select ticket run to inspect
tickets = st.session_state.get("tickets_db", [])
ticket_ids = [t["id"] for t in tickets]
selected_id = st.selectbox("Select Ticket Run to Inspect", ticket_ids)

st.markdown("### 📊 Execution Plan & Dynamic DAG Topology")

col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("#### Planned Dependency Graph")
    # Live workflow visualization animation mock
    st.info("💡 Click animate below to trace dynamic execution through the LangGraph StateGraph.")
    
    if st.button("Animate Workflow Execution Path"):
        progress_bar = st.progress(0.0)
        status_text = st.empty()
        
        steps = [
            (0.1, "🚀 Executing Planner Node..."),
            (0.3, "📥 Classifying categories (Triage Agent)..."),
            (0.5, "🔎 Fetching policies and vector documents (Research Agent)..."),
            (0.7, "✏️ Synthesizing draft responses (Draft Agent)..."),
            (0.9, "🛡️ Running security and fact-checking checks (FactChecker)..."),
            (1.0, "🎯 Routing to Human Review Gate.")
        ]
        
        for p, txt in steps:
            time.sleep(0.3)
            progress_bar.progress(p)
            status_text.markdown(f"**Current Node**: {txt}")
            
        st.success("Workflow Execution Completed successfully!")

    st.markdown("""
    **State graph edges structure**:
    - `START` → `Planner`
    - `Planner` → `Coordinator`
    - `Coordinator` → `Triage` & `Research` (Parallel fork)
    - `Triage` & `Research` → `Coordinator` (Fan-in wait join)
    - `Coordinator` → `Draft`
    - `Draft` → `Coordinator`
    - `Coordinator` → `FactChecker`
    - `FactChecker` → `Coordinator`
    - `Coordinator` → `Confidence` → `HumanReview` → `Execute` → `END`
    """)

with col2:
    st.markdown("#### LLM Planner Output Variables")
    planner_payload = {
        "active_agents": ["Triage", "Research", "Draft", "FactChecker"],
        "dependencies": {
            "Draft": ["Triage", "Research"],
            "FactChecker": ["Draft"]
        },
        "required_tools": ["db_tool"],
        "confidence_threshold": 80.0,
        "human_review_requirement": True,
        "estimated_cost": 0.034
    }
    st.json(planner_payload)

st.markdown("---")

st.subheader("⏱️ Execution Timeline & Metrics")

col3, col4 = st.columns(2)

with col3:
    st.markdown("#### Agent Execution Latency (Gantt representation)")
    # Renders timeline stats
    st.markdown("""
    - **Planner**: `■■■■` 820ms
    - **Triage**: `■` 210ms
    - **Research**: `■■■■■■` 1200ms
    - **Draft**: `■■■■■■■■` 1500ms
    - **FactChecker**: `■■■■■■■■■` 1800ms
    """)

with col4:
    st.markdown("#### Processing Run Statistics")
    st.markdown("""
    - **Total Latency**: `5.53s`
    - **Prompt Tokens**: `14,202`
    - **Completion Tokens**: `2,840`
    - **Total Tokens**: `17,042`
    - **Estimated Session Cost**: `$0.0342`
    """)

st.markdown("---")
st.subheader("💬 Node Payloads Input / Output Inspector")

agent_selected = st.selectbox("Select Agent Node to Inspect Payloads", ["Planner", "Triage", "Research", "Draft", "FactChecker"])

payloads = {
    "Planner": {
        "input": "Ticket query text CS-4322 subscription refunds.",
        "output": planner_payload
    },
    "Triage": {
        "input": "Ticket text contents.",
        "output": {"category": "billing", "priority": "high", "sentiment": "neutral", "urgency": "medium"}
    },
    "Research": {
        "input": "Reference chunks from refund policies.",
        "output": "Summarized policies detail matching 30 day window limits."
    },
    "Draft": {
        "input": "Triage inputs and policy matches.",
        "output": "We received your refund request. Subscriptions are refundable within 30 days..."
    },
    "FactChecker": {
        "input": "Draft response and original reference chunks.",
        "output": {"verified_claims": ["Refunds refundable within 30 days"], "unverified_claims": [], "hallucination_risk": 0.05}
    }
}

col_in, col_out = st.columns(2)
with col_in:
    st.markdown("**Node Input Context Payload**:")
    st.info(payloads[agent_selected]["input"])
with col_out:
    st.markdown("**Node Output Response Payload**:")
    st.json(payloads[agent_selected]["output"])

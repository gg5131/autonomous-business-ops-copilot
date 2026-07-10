"""Main Streamlit app entrypoint implementing Role Selector gate controls."""

from __future__ import annotations

import streamlit as st

st.set_page_config(
    page_title="Autonomous Business Ops Copilot",
    page_icon="🤖",
    layout="wide",
)

from frontend.utils.state_helpers import init_session_state

# Initialize session structures
init_session_state()

st.title("🤖 Autonomous Business Operations Copilot")
st.markdown("### Enterprise Multi-Agent AI System Dashboard")

st.markdown("---")

col1, col2 = st.columns([1, 1])

with col1:
    st.info("💡 **Welcome to the Copilot Console**\nPlease select your enterprise role to proceed. Access rights are dynamically updated based on your selected role.")
    
    role = st.selectbox(
        "Select User Role",
        ["Admin", "Reviewer", "Auditor"],
        index=1,
    )
    
    if st.button("Enter Console", use_container_width=True):
        st.session_state["user_role"] = role
        st.session_state["user_logged_in"] = True
        st.success(f"Success: Logged in with role **{role}**! Use the sidebar navigation to explore features.")

with col2:
    st.markdown("#### Role Capabilities Guide")
    st.markdown("""
    - 🛡️ **Admin**: Full access. Clear caches, configure thresholds, modify system parameters.
    - 📥 **Reviewer**: Handle human-in-the-loop approvals. Review response drafts, edit content, and resolve tickets.
    - 🔍 **Auditor**: Read-only access. Inspect logs, memory modules, and run explainability pathways.
    """)

st.markdown("---")
st.caption("Autonomous Business Operations Copilot v1.0.0 — Google Gemini & LangGraph Powered.")

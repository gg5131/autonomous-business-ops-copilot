"""Settings configuration page."""

from __future__ import annotations

import streamlit as st
from frontend.utils.state_helpers import init_session_state, get_current_role, inject_custom_css

st.set_page_config(page_title="Settings", page_icon="⚙️", layout="wide")
init_session_state()
inject_custom_css()

if not st.session_state.get("user_logged_in", False):
    st.warning("⚠️ Access Denied: Please log in at the main page first.")
    st.stop()

st.title("⚙️ System Settings")
st.markdown(f"Active Role Session: **{get_current_role()}**")


st.markdown("---")

# Verify access level
if get_current_role() not in ["Admin", "Reviewer"]:
    st.error("Access Denied: You do not have permissions to modify system configurations.")
else:
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### LLM model configurations")
        model = st.selectbox(
            "Selected Reasoning Model",
            ["gemini-2.5-flash", "gemini-2.5-pro"],
            index=0 if st.session_state["selected_model"] == "gemini-2.5-flash" else 1
        )
        temp = st.slider("LLM Generation Temperature", 0.0, 1.0, 0.2, 0.05)
        
        st.markdown("#### Dynamic thresholds")
        conf_t = st.slider(
            "Target Confidence Autopilot Threshold", 
            50.0, 100.0, 
            st.session_state["confidence_threshold"],
            1.0
        )
        
    with col2:
        st.markdown("#### Active Agents configurations")
        st.checkbox("Triage Agent", value=True)
        st.checkbox("Research Agent", value=True)
        st.checkbox("Policy Agent", value=True)
        st.checkbox("CustomerHistory Agent", value=True)
        st.checkbox("Draft Response Agent", value=True)
        st.checkbox("FactChecker Agent", value=True)
        st.checkbox("Security Agent", value=True)
        
    if st.button("Save Settings Profile", type="primary"):
        st.session_state["selected_model"] = model
        st.session_state["confidence_threshold"] = conf_t
        st.success("Configurations saved successfully!")

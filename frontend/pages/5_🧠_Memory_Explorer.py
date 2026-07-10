"""Memory Explorer page rendering segmented memory types."""

from __future__ import annotations

import streamlit as st
from frontend.utils.state_helpers import init_session_state, get_current_role, inject_custom_css

st.set_page_config(page_title="Memory Explorer", page_icon="🧠", layout="wide")
init_session_state()
inject_custom_css()

if not st.session_state.get("user_logged_in", False):
    st.warning("⚠️ Access Denied: Please log in at the main page first.")
    st.stop()

st.title("🧠 Memory Explorer")
st.markdown(f"Active Role Session: **{get_current_role()}**")


st.markdown("---")

search_term = st.text_input("Search Concepts or Ticket Logs inside memory stores", "")

# Load mock memories from session state
mem_db = st.session_state.get("memories_db", {})

t_episodic, t_semantic, t_procedural, t_feedback = st.tabs([
    "📥 Episodic Memory", 
    "📚 Semantic Memory", 
    "🛠️ Procedural Memory", 
    "💬 Feedback Memory"
])

with t_episodic:
    st.markdown("#### Episodic Memory (Direct query and response logs history)")
    records = mem_db.get("episodic", [])
    if search_term:
        records = [r for r in records if search_term.lower() in str(r).lower()]
    st.write(records)

with t_semantic:
    st.markdown("#### Semantic Memory (Domain ontology definitions and concept profiles)")
    records = mem_db.get("semantic", [])
    if search_term:
        records = [r for r in records if search_term.lower() in str(r).lower()]
    st.write(records)
    
    # Allow adding new facts if Admin
    if get_current_role() == "Admin":
        st.markdown("---")
        st.markdown("##### 🛡️ Add Concept Fact Profile (Admin only)")
        concept = st.text_input("Concept Name", "")
        definition = st.text_area("Concept Definition", "")
        if st.button("Store Concept Fact"):
            if concept and definition:
                mem_db["semantic"].append({
                    "concept": concept,
                    "definition": definition,
                    "timestamp": "2026-07-10T15:00:00Z"
                })
                st.success("New fact profile loaded into semantic memory!")
                st.rerun()

with t_procedural:
    st.markdown("#### Procedural Memory (General guidelines and agent workflow strategies)")
    records = mem_db.get("procedural", [])
    if search_term:
        records = [r for r in records if search_term.lower() in str(r).lower()]
    st.write(records)

with t_feedback:
    st.markdown("#### Feedback Memory (Human corrections deltas and edits histories)")
    records = mem_db.get("feedback", [])
    if search_term:
        records = [r for r in records if search_term.lower() in str(r).lower()]
    st.write(records)

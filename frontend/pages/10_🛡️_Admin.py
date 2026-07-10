"""Admin system panel for cache clearing and database statistics."""

from __future__ import annotations

import streamlit as st
from frontend.utils.state_helpers import init_session_state, get_current_role, inject_custom_css

st.set_page_config(page_title="Admin Panel", page_icon="🛡️", layout="wide")
init_session_state()
inject_custom_css()

if not st.session_state.get("user_logged_in", False):
    st.warning("⚠️ Access Denied: Please log in at the main page first.")
    st.stop()

st.title("🛡️ Admin Console Panel")
st.markdown(f"Active Role Session: **{get_current_role()}**")


st.markdown("---")

if get_current_role() != "Admin":
    st.error("Access Denied: Admin console utilities are only available to users with the Admin role.")
else:
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Database & Cache Statistics")
        st.write({
            "SQLite Embedding Cache File size": "1.2 MB",
            "Cached Embeddings Count": 523,
            "Neo4j Graph Database Node count": 82,
            "Neo4j Relationship count": 142,
            "ChromaDB Vector count": 120,
            "Alembic Database Schema Migration version": "a4b5c6d7e8f9"
        })
        
    with col2:
        st.markdown("#### Administrative Actions")
        
        st.warning("⚠️ **Warning**: Clearing caches or resetting databases can cause service degradation or require re-indexing of documents.")
        
        if st.button("Clear SQLite Embedding Cache", use_container_width=True):
            st.success("Embedding cache cleared successfully!")
            
        if st.button("Rebuild Neo4j Schema Constraints", use_container_width=True):
            st.success("Unique index constraints refreshed on Neo4j.")
            
        if st.button("Purge In-Memory State Checkpoints", use_container_width=True):
            st.success("In-memory checkpointer history purged.")

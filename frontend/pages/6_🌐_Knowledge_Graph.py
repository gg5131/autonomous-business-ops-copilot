"""Knowledge Graph Explorer page visualizing Neo4j entity networks and Leiden partitions."""

from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components
from frontend.utils.state_helpers import init_session_state, get_current_role, inject_custom_css

st.set_page_config(page_title="Knowledge Graph Explorer", page_icon="🌐", layout="wide")
init_session_state()
inject_custom_css()

if not st.session_state.get("user_logged_in", False):
    st.warning("⚠️ Access Denied: Please log in at the main page first.")
    st.stop()

st.title("🌐 Knowledge Graph Explorer")
st.markdown(f"Active Role Session: **{get_current_role()}**")


st.markdown("---")

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("🔍 Search Entities & Relations")
    search_q = st.text_input("Enter node label or entity name", "Refund Policy")
    
    st.markdown("#### Leiden Community Partitions")
    st.info("💡 Nodes are colored and grouped dynamically into Leiden communities based on density.")
    
    st.markdown("""
    - **Community #1**: Refund policies and Billing configurations (member count: `12`)
    - **Community #2**: API Gateway systems and OAuth access rules (member count: `8`)
    - **Community #3**: Customer tier priorities and SLA definitions (member count: `15`)
    """)

with col2:
    st.subheader("🕸️ Graph Network Visualizer")
    
    # Renders a neat interactive network placeholder
    # In production pyvis compiles to HTML and renders inside components.html()
    # We can write an SVG/HTML visualization mockup here
    html_code = """
    <div style="background-color: #1e2430; border: 1px solid #2d3748; border-radius: 8px; padding: 40px; text-align: center; color: #e2e8f0; font-family: sans-serif;">
        <h3 style="color: #38bdf8;">Interactive Neo4j Entity Network Visualization</h3>
        <p>Representing local relationships around: <b>Refund Policy</b></p>
        <div style="margin: 20px auto; width: 300px; height: 300px; border-radius: 50%; border: 2px dashed #38bdf8; position: relative;">
            <div style="position: absolute; top: 135px; left: 90px; padding: 10px; background: #0369a1; border-radius: 5px; font-weight: bold; font-size: 12px;">Refund Policy</div>
            <div style="position: absolute; top: 30px; left: 40px; padding: 5px; background: #065f46; border-radius: 5px; font-size: 11px;">CloudSync Pro</div>
            <div style="position: absolute; top: 230px; left: 160px; padding: 5px; background: #3730a3; border-radius: 5px; font-size: 11px;">Customer Success</div>
            
            <!-- Lines -->
            <div style="position: absolute; top: 80px; left: 100px; width: 2px; height: 60px; background: #2d3748; transform: rotate(-30deg);"></div>
            <div style="position: absolute; top: 170px; left: 140px; width: 2px; height: 65px; background: #2d3748; transform: rotate(40deg);"></div>
        </div>
        <p style="font-size: 12px; color: #94a3b8;">Click nodes to inspect attributes and connections.</p>
    </div>
    """
    components.html(html_code, height=450)

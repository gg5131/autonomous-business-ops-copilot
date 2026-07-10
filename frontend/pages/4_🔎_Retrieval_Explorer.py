"""Retrieval Explorer page visualizing the hybrid search sequence pipelines."""

from __future__ import annotations

import streamlit as st
from frontend.utils.state_helpers import init_session_state, get_current_role, inject_custom_css

st.set_page_config(page_title="Retrieval Explorer", page_icon="🔎", layout="wide")
init_session_state()
inject_custom_css()

if not st.session_state.get("user_logged_in", False):
    st.warning("⚠️ Access Denied: Please log in at the main page first.")
    st.stop()

st.title("🔎 Retrieval Explorer")
st.markdown(f"Active Role Session: **{get_current_role()}**")


st.markdown("---")

query = st.text_input("Enter Query to Test Search Pipeline", "refund policy subscription window")

if query:
    st.markdown("### 🔍 Hybrid Retrieval Step-by-Step Visualization")
    
    # Render steps
    with st.expander("Step 1: BM25 Sparse Search Match Candidates", expanded=True):
        bm25_matches = [
            {"id": "doc_refund_policy", "content": "Refund policy states subscriptions are refundable within 30 days.", "score": 12.8},
            {"id": "doc_sla", "content": "Support SLAs for enterprise accounts is 4 hours response.", "score": 2.1}
        ]
        st.write(bm25_matches)
        
    with st.expander("Step 2: ChromaDB Dense Vector Search Candidates", expanded=True):
        vector_matches = [
            {"id": "doc_refund_policy", "content": "Refund policy details subscriptions refundable within 30 days.", "score": 0.89},
            {"id": "doc_billing_cycles", "content": "Subscriptions bill monthly on date of purchase.", "score": 0.65}
        ]
        st.write(vector_matches)
        
    with st.expander("Step 3: Neo4j Graph Search Entities & Connections", expanded=True):
        graph_matches = [
            {"entity": "Policy: Refund Policy", "relationship": "APPLIES_TO", "target": "Product: CloudSync Pro", "confidence": 0.95},
            {"entity": "Department: Legal", "relationship": "CREATES", "target": "Policy: Refund Policy", "confidence": 0.9}
        ]
        st.write(graph_matches)
        
    with st.expander("Step 4: Reciprocal Rank Fusion (RRF) Candidates Merger", expanded=True):
        rrf_results = [
            {"id": "doc_refund_policy", "combined_score": 0.033, "source_ranks": {"bm25": 1, "vector": 1}},
            {"id": "doc_billing_cycles", "combined_score": 0.016, "source_ranks": {"vector": 2}},
            {"id": "doc_sla", "combined_score": 0.016, "source_ranks": {"bm25": 2}}
        ]
        st.write(rrf_results)
        
    with st.expander("Step 5: Cross-Encoder Reranker Final Selection", expanded=True):
        reranked = [
            {"id": "doc_refund_policy", "content": "Refund policy states subscriptions are refundable within 30 days.", "score": 0.985},
            {"id": "doc_billing_cycles", "content": "Subscriptions bill monthly on date of purchase.", "score": 0.420}
        ]
        st.write(reranked)
        
    st.markdown("### 🏆 Final Assembled Context Payload")
    final_ctx = "\n".join([f"### Document: {r['id']}\n{r['content']}" for r in reranked])
    st.code(final_ctx, language="markdown")

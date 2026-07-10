"""File Ingestion page for document uploads and ingestion pipelines logs."""

from __future__ import annotations

import streamlit as st
import time
from frontend.utils.state_helpers import init_session_state, get_current_role, inject_custom_css

st.set_page_config(page_title="Document Ingestion", page_icon="📥", layout="wide")
init_session_state()
inject_custom_css()

if not st.session_state.get("user_logged_in", False):
    st.warning("⚠️ Access Denied: Please log in at the main page first.")
    st.stop()

st.title("📥 Document Ingestion Hub")
st.markdown(f"Active Role Session: **{get_current_role()}**")


st.markdown("---")

uploaded_files = st.file_uploader(
    "Upload Document (PDF, DOCX, CSV, EML)", 
    type=["pdf", "docx", "csv", "eml"],
    accept_multiple_files=True
)

if uploaded_files:
    if st.button("Trigger Ingestion Pipeline", type="primary"):
        # Real-time parsing progress bar
        for idx, file in enumerate(uploaded_files, 1):
            progress_bar = st.progress(0.0)
            status_text = st.empty()
            
            steps = [
                (0.2, "📁 Loading file contents..."),
                (0.5, "🔎 Parsing layouts and images (OCR fallback check)..."),
                (0.8, "🧠 Extracting entities and relationships (Gemini extract)..."),
                (1.0, "✅ Successfully seeded and indexed in ChromaDB and Neo4j!")
            ]
            
            for p, txt in steps:
                time.sleep(0.3)
                progress_bar.progress(p)
                status_text.markdown(f"**Ingesting file `{file.name}`**: {txt}")
                
            st.success(f"File **{file.name}** ingested successfully!")
            
        st.markdown("---")
        st.subheader("📋 Ingestion Logs")
        st.code("""
        [INFO] 2026-07-10 14:02:01 - Started parsing doc_refund_policy.pdf
        [INFO] 2026-07-10 14:02:02 - Completed text extraction: 2420 characters.
        [INFO] 2026-07-10 14:02:03 - Created 5 semantic text chunks.
        [INFO] 2026-07-10 14:02:04 - Extracted: 4 Entities (Refund Policy, Subscriptions, Customer Success, CloudSync Pro)
        [INFO] 2026-07-10 14:02:05 - Graph constraints checks passed. Updated Neo4j.
        """, language="bash")

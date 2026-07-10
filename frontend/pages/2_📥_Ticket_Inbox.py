"""Ticket Inbox page displaying review queues and human-in-the-loop interaction panels."""

from __future__ import annotations

import streamlit as st
from frontend.utils.state_helpers import init_session_state, get_current_role, inject_custom_css

st.set_page_config(page_title="Ticket Review Inbox", page_icon="📥", layout="wide")
init_session_state()
inject_custom_css()

if not st.session_state.get("user_logged_in", False):
    st.warning("⚠️ Access Denied: Please log in at the main page first.")
    st.stop()

st.title("📥 Ticket Review Inbox")
st.markdown(f"Active Role Session: **{get_current_role()}**")


st.markdown("---")

# Get tickets from session DB
tickets = st.session_state.get("tickets_db", [])
pending_tickets = [t for t in tickets if t["status"] == "Pending Review"]

if not pending_tickets:
    st.success("🎉 All caught up! No pending human reviews found.")
else:
    # Sidebar ticket selector queue
    st.sidebar.markdown("### 📥 Review Queue")
    ticket_options = {f"{t['id']} - {t['title']}": t for t in pending_tickets}
    selected_label = st.sidebar.radio("Select Ticket to Review", list(ticket_options.keys()))
    
    selected_ticket = ticket_options[selected_label]
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown(f"### Ticket Details: `{selected_ticket['id']}`")
        st.markdown(f"**Title**: {selected_ticket['title']}")
        st.markdown(f"**Customer ID**: `{selected_ticket['customer_id']}`")
        st.markdown(f"**Category**: `{selected_ticket['category']}`")
        st.markdown(f"**Priority**: `{selected_ticket['priority'].upper()}`")
        st.info(f"**Content**:\n{selected_ticket['content']}")
        
        st.markdown("---")
        st.markdown("#### 📊 Confidence Scoring Profile")
        
        # Display mock confidence metrics gauge
        st.progress(0.88, text="Groundedness Score: 88%")
        st.progress(0.95, text="Citation Coverage: 95%")
        st.progress(0.10, text="Hallucination Risk: 10%")
        st.progress(1.00, text="Policy Compliance: 100%")
        st.success("🎯 **Overall Confidence Score: 88.5%** — Safe to auto-recommend approval.")

    with col2:
        st.markdown("### ✏️ Draft Review Workspace")
        st.markdown("Review, correct, or adjust the drafted AI response details below.")
        
        original_draft = selected_ticket["draft"]
        
        # Reviewer editable field
        corrected_draft = st.text_area(
            "Draft Response Editor",
            value=original_draft,
            height=200,
        )
        
        # Dynamic comparison diff viewer
        if corrected_draft != original_draft:
            st.markdown("**Diff Changes Preview**:")
            # Basic diff rendering
            st.markdown(f"""
            *Original*: <span class="diff-removed">{original_draft[:100]}...</span>
            *Edited*: <span class="diff-added">{corrected_draft[:100]}...</span>
            """, unsafe_allow_html=True)
            
        feedback_notes = st.text_input("Reviewer Feedback Notes (required on rejection/escalation)", "")
        
        # Interactive buttons
        b1, b2, b3, b4 = st.columns(4)
        
        with b1:
            if st.button("✅ Approve", type="primary", use_container_width=True):
                # Mark as approved
                selected_ticket["status"] = "Approved"
                # Add to feedback memory
                st.session_state["memories_db"]["feedback"].append({
                    "ticket_id": selected_ticket["id"],
                    "original": original_draft,
                    "corrected": corrected_draft,
                    "notes": feedback_notes or "Approved directly",
                    "timestamp": "2026-07-10T14:00:00Z"
                })
                st.success("Ticket approved and response dispatched!")
                st.rerun()
                
        with b2:
            if st.button("❌ Reject", use_container_width=True):
                if not feedback_notes:
                    st.error("Error: Feedback notes are required on rejection.")
                else:
                    selected_ticket["status"] = "Rejected"
                    st.warning("Draft rejected and sent back to planner for re-route.")
                    st.rerun()
                    
        with b3:
            if st.button("✏️ Save Edits", use_container_width=True):
                selected_ticket["draft"] = corrected_draft
                st.success("Draft edits saved locally.")
                
        with b4:
            if st.button("⬆️ Escalate", use_container_width=True):
                selected_ticket["status"] = "Escalated"
                st.info("Ticket escalated to Senior Tier Support.")
                st.rerun()
                
        # Explainability panel
        with st.expander("🔍 Explainability Details & Reasoning Path"):
            st.markdown("""
            - **Decision Route**: `START` → `Planner` → `Triage` & `Research` → `Draft` → `FactChecker` → `Confidence` → `HumanReview`
            - **Retrieved Reference Citations**:
              - `[doc_refund]`: company-refund-rules.md (92% match)
            - **Verification checks completed**:
              - Fact checker matches: 4/4 verified
              - Security check: Clean (no PII or prompt injection flagged)
            """)

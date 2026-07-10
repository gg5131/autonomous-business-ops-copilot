"""State helpers tracking Streamlit roles, active ticket buffers, and user configurations."""

from __future__ import annotations

from typing import Any, Dict, List
import streamlit as st


def init_session_state() -> None:
    """Pre-populates required session keys if not already initialized."""
    if "user_role" not in st.session_state:
        st.session_state["user_role"] = "Reviewer"  # Default selector role
    if "user_logged_in" not in st.session_state:
        st.session_state["user_logged_in"] = False
    if "active_ticket_id" not in st.session_state:
        st.session_state["active_ticket_id"] = None
    if "confidence_threshold" not in st.session_state:
        st.session_state["confidence_threshold"] = 80.0
    if "selected_model" not in st.session_state:
        st.session_state["selected_model"] = "gemini-2.5-flash"

    # Mock DB storage in session to allow standalone front-end play
    if "tickets_db" not in st.session_state:
        st.session_state["tickets_db"] = [
            {
                "id": "t1",
                "title": "Refund request CS-4322",
                "content": "Requested refund for CloudSync Pro subscription. Window expired 2 days ago.",
                "customer_id": "c100",
                "category": "billing",
                "status": "Pending Review",
                "priority": "high",
                "draft": "We received your refund request for ticket [t1]. According to standard policy [doc0], subscriptions are refundable within 30 days.",
            },
            {
                "id": "t2",
                "title": "Access request API Gateway",
                "content": "Need production write access for developer keys.",
                "customer_id": "c101",
                "category": "account_access",
                "status": "Pending Review",
                "priority": "medium",
                "draft": "Regarding access request [t2], dev keys must complete security signoffs.",
            },
        ]

    if "memories_db" not in st.session_state:
        st.session_state["memories_db"] = {
            "episodic": [
                {"ticket_id": "t1", "plan": "Planner executed Triage -> Draft", "timestamp": "2026-07-10T12:00:00Z"},
            ],
            "semantic": [
                {"concept": "CloudSync Pro", "definition": "Enterprise file storage subscription model", "timestamp": "2026-07-10T11:00:00Z"},
            ],
            "procedural": [
                {"procedure": "Billing Dispute", "steps": ["Check purchase history", "Inspect refund policy", "Formulate draft"], "timestamp": "2026-07-10T10:00:00Z"},
            ],
            "feedback": [
                {"ticket_id": "t1", "edit_delta": "Revised refund window eligibility wording.", "timestamp": "2026-07-10T13:00:00Z"},
            ],
        }


def get_current_role() -> str:
    """Returns currently selected user role."""
    return str(st.session_state.get("user_role", "Reviewer"))


def is_role_authorized(allowed_roles: List[str]) -> bool:
    """Assert if current role is authorized."""
    return get_current_role() in allowed_roles


def inject_custom_css() -> None:
    """Loads styles/main.css dynamically and injects it as an HTML style tag."""
    import os
    css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "styles", "main.css")
    if os.path.exists(css_path):
        try:
            with open(css_path, "r", encoding="utf-8") as f:
                css_content = f.read()
            st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
        except Exception:
            pass


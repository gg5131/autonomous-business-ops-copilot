"""Orchestrator state definitions with custom reducer merges."""

from __future__ import annotations

import operator
from typing import Annotated, Any, Dict, List, TypedDict

from src.agents.planner import ExecutionPlan


def merge_dicts(existing: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
    """Helper reducer merging dictionaries without overwriting sibling keys."""
    return {**(existing or {}), **(new or {})}


class CopilotState(TypedDict):
    """Execution state tracking ticket variables, plans, results and log actions."""

    # Ticket inputs
    ticket_id: str
    ticket_title: str
    ticket_content: str
    customer_id: str

    # Execution Plan DAG
    execution_plan: ExecutionPlan
    executed_agents: Annotated[List[str], operator.add]
    scheduled_agents: Annotated[List[str], operator.add]
    next_agent: str


    # Context & Memory references
    retrieved_context: List[Dict[str, Any]]
    memory_context: List[Dict[str, Any]]

    # Agent Execution Results
    agent_results: Annotated[Dict[str, Any], merge_dicts]
    validation_results: Annotated[Dict[str, Any], merge_dicts]

    # Draft Responses
    draft_response: str
    confidence_scores: Dict[str, float]

    # Human Review decisions
    review_decision: str  # approved, edited, rejected
    reviewer_feedback: str
    reviewer_id: str

    # Observability
    trace_id: str
    audit_trail: Annotated[List[Dict[str, Any]], operator.add]

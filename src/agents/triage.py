"""Triage Agent classifying incoming customer tickets."""

from __future__ import annotations

import json
from typing import Any, Dict

from src.agents.base import BaseAgent
from src.orchestrator.agent_context import AgentContext
from src.orchestrator.llm_gateway import LLMGateway


class TriageAgent(BaseAgent):
    """Classifies ticket categories, urgencies, and customer sentiments."""

    def __init__(self, llm_gateway: LLMGateway) -> None:
        super().__init__(llm_gateway)

    @property
    def name(self) -> str:
        return "Triage"

    @property
    def system_prompt_key(self) -> str:
        return "triage_system_prompt"

    def validate_input(self, context: AgentContext) -> None:
        if not context.ticket or not context.ticket.get("content"):
            raise ValueError("Triage Agent requires ticket content to analyze.")

    def validate_output(self, context: AgentContext, response: Dict[str, Any]) -> None:
        super().validate_output(context, response)
        try:
            data = json.loads(response["text"])
            required = ["category", "priority", "sentiment", "urgency"]
            for field in required:
                if field not in data:
                    raise KeyError(f"Missing required classification field: {field}")
        except Exception as e:
            raise ValueError(f"Triage Agent response failed category schema checks: {e}")

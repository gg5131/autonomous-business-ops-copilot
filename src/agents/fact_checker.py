"""Fact Checker Agent verifying response draft statements against ground-truth contexts."""

from __future__ import annotations

import json
from typing import Any, Dict

from src.agents.base import BaseAgent
from src.orchestrator.agent_context import AgentContext
from src.orchestrator.llm_gateway import LLMGateway


class FactCheckerAgent(BaseAgent):
    """Asserts facts and computes groundedness and hallucination risk scores."""

    def __init__(self, llm_gateway: LLMGateway) -> None:
        super().__init__(llm_gateway)

    @property
    def name(self) -> str:
        return "FactChecker"

    @property
    def system_prompt_key(self) -> str:
        return "fact_checker_system_prompt"

    def validate_input(self, context: AgentContext) -> None:
        draft = context.ticket.get("draft_response")
        if not draft:
            raise ValueError("FactChecker Agent requires a draft response to verify.")

    def build_context(self, context: AgentContext) -> str:
        base_ctx = super().build_context(context)
        draft = context.ticket.get("draft_response", "")
        return f"{base_ctx}\n\n## Response Draft to Verify:\n{draft}"

    def validate_output(self, context: AgentContext, response: Dict[str, Any]) -> None:
        super().validate_output(context, response)
        try:
            data = json.loads(response["text"])
            required = ["verified_claims", "unverified_claims", "hallucination_risk"]
            for field in required:
                if field not in data:
                    raise KeyError(f"Missing required fact checks field: {field}")
            # Ensure hallucination_risk is a float between 0.0 and 1.0
            float(data["hallucination_risk"])
        except Exception as e:
            raise ValueError(f"FactChecker Agent response failed schema validation: {e}")

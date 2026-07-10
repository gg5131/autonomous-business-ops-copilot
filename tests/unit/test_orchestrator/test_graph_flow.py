"""Unit tests verifying the multi-agent graph flow, dynamic routers, and checkpointers."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from langgraph.checkpoint.memory import MemorySaver

from src.agents.planner import ExecutionPlan, PlannerAgent
from src.agents.triage import TriageAgent
from src.confidence.engine import ConfidenceEngine
from src.orchestrator.agent_context import AgentContext
from src.orchestrator.event_bus import SystemEvent, event_bus
from src.orchestrator.graph import build_orchestrator_graph
from src.orchestrator.state import CopilotState
from src.tools.registry import registry


@pytest.mark.asyncio
async def test_planner_agent_plan_generation() -> None:
    """Validate that the PlannerAgent generates a valid ExecutionPlan JSON structure."""
    mock_llm = MagicMock()
    # Mock successful LLM plan generation
    mock_plan = {
        "active_agents": ["Triage", "Research", "Draft"],
        "dependencies": {"Draft": ["Triage", "Research"]},
        "parallel_groups": [["Triage", "Research"]],
        "required_tools": ["slack_webhook"],
        "confidence_threshold": 80.0,
        "human_review_requirement": True,
        "estimated_cost": 0.04,
    }
    mock_llm.generate_response = AsyncMock(
        return_value={
            "text": json.dumps(mock_plan),
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150,
            "cost_usd": 0.04,
            "latency_ms": 120.0,
        }
    )

    planner = PlannerAgent(llm_gateway=mock_llm)
    context = AgentContext(
        ticket={"content": "Billing query from customer CS-123"},
        execution_plan={},
        retrieved_context=[],
        memory_context=[],
        tool_registry=registry,
        trace_id="test-trace-123",
        logger=MagicMock(),
    )

    plan = await planner.execute_plan_generation(context)
    assert plan.active_agents == ["Triage", "Research", "Draft"]
    assert plan.dependencies["Draft"] == ["Triage", "Research"]
    assert plan.confidence_threshold == 80.0


def test_confidence_engine_scoring() -> None:
    """Validate calculations for citation coverage, groundedness, and overall confidence scores."""
    engine = ConfidenceEngine()
    draft = "According to policy [doc_refund] refund window is 30 days. No refunds after that [doc_refund]."
    sources = [{"id": "doc_refund", "content": "Company refund policy is 30 days after date of purchase."}]
    fact_checker_output = {"hallucination_risk": 0.1}

    scores = engine.compute_score(
        draft=draft,
        sources=sources,
        fact_checker_output=fact_checker_output,
        compliance_passed=True,
    )

    assert scores["overall_confidence"] > 50.0
    assert scores["citation_coverage"] == 100.0


@pytest.mark.asyncio
async def test_full_orchestration_workflow() -> None:
    """Test full multi-agent state graph transitions using MemorySaver checkpointer."""
    # 1. Compile graph with checkpointer
    memory = MemorySaver()
    app = build_orchestrator_graph().compile(checkpointer=memory)

    # 2. Setup mock LLM answers for all nodes
    mock_plan = {
        "active_agents": ["Triage", "Draft"],
        "dependencies": {"Draft": ["Triage"]},
        "parallel_groups": [["Triage"]],
        "required_tools": [],
        "confidence_threshold": 80.0,
        "human_review_requirement": True,
        "estimated_cost": 0.02,
    }

    mock_responses = [
        # Planner response
        json.dumps(mock_plan),
        # Triage response
        json.dumps({"category": "billing", "priority": "high", "sentiment": "neutral", "urgency": "medium"}),
        # Draft response
        "Draft customer response: refunds are processed in [doc_refund] days.",
    ]

    with patch("src.orchestrator.graph.llm_gateway.generate_response") as mock_gen:
        async def mock_generate(prompt: str, **kwargs: Any) -> Dict[str, Any]:
            # Identify caller based on system instruction content
            system_inst = kwargs.get("system_instruction", "").lower()
            if "planner" in system_inst:
                text = mock_responses[0]
            elif "triage" in system_inst:
                text = mock_responses[1]
            else:
                text = mock_responses[2]
            return {
                "text": text,
                "prompt_tokens": 10,
                "completion_tokens": 10,
                "total_tokens": 20,
                "cost_usd": 0.01,
                "latency_ms": 10.0,
            }


        mock_gen.side_effect = mock_generate

        # Define initial state
        initial_state = CopilotState(
            ticket_id="ticket-100",
            ticket_title="Billing Help",
            ticket_content="Need a billing extension",
            customer_id="cust-200",
            retrieved_context=[{"id": "doc_refund", "content": "extension is 14 days"}],
            memory_context=[],
            trace_id="test-trace-uuid",
            executed_agents=[],
            scheduled_agents=[],
            next_agent="",
            agent_results={},
            validation_results={},
            audit_trail=[],
        )


        config = {"configurable": {"thread_id": "thread-1"}}

        # Start execution. Since there is an interrupt at human_review, it should pause there
        try:
            # We catch GraphInterrupt or run step by step
            await app.ainvoke(initial_state, config=config)
        except Exception as e:
            # Reaching interrupt is the expected outcome!
            assert "human_review" in str(e) or "Interrupt" in type(e).__name__

        # Inspect current state checkpoint
        state_info = await app.aget_state(config)
        assert state_info.values["execution_plan"].active_agents == ["Triage", "Draft"]
        assert "Triage" in state_info.values["executed_agents"]
        assert "Draft" in state_info.values["executed_agents"]
        assert state_info.values["draft_response"] != ""

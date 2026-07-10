"""Main StateGraph builder compiling dynamic agent nodes and checkpointers."""

from __future__ import annotations

import operator
from typing import Any, Dict, List, Union
from langgraph.graph import END, START, StateGraph

from configs.settings import get_settings
from src.agents.base import BaseAgent
from src.agents.planner import PlannerAgent, ExecutionPlan
from src.agents.triage import TriageAgent
from src.agents.research import ResearchAgent
from src.agents.policy import PolicyAgent
from src.agents.draft import DraftAgent
from src.agents.fact_checker import FactCheckerAgent
from src.confidence.engine import ConfidenceEngine
from src.orchestrator.agent_context import AgentContext
from src.orchestrator.event_bus import SystemEvent, event_bus
from src.orchestrator.llm_gateway import LLMGateway
from src.orchestrator.state import CopilotState
from src.tools.registry import registry
from src.observability.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Initialize shared gateway
llm_gateway = LLMGateway()


async def planner_node(state: CopilotState) -> Dict[str, Any]:
    """Runs planner to build execution plan DAG."""
    context = AgentContext(
        ticket={"content": state["ticket_content"]},
        execution_plan={},
        retrieved_context=state["retrieved_context"],
        memory_context=state["memory_context"],
        tool_registry=registry,
        trace_id=state["trace_id"],
        logger=logger,
    )
    planner = PlannerAgent(llm_gateway=llm_gateway)
    plan = await planner.execute_plan_generation(context)
    return {
        "execution_plan": plan,
        "executed_agents": [],
        "scheduled_agents": [],
        "next_agent": "",
        "audit_trail": [{"action": "Created execution plan", "plan": plan.dict()}],
    }


async def coordinator_node(state: CopilotState) -> Dict[str, Any]:
    """Evaluates plan dependencies, registers scheduled tasks, and manages deadlock overrides."""
    plan: ExecutionPlan = state["execution_plan"]
    executed: List[str] = state.get("executed_agents", []) or []
    scheduled: List[str] = state.get("scheduled_agents", []) or []
    active_agents = plan.active_agents
    dependencies = plan.dependencies

    # Find agents that are ready (all dependencies completed and not scheduled yet)
    ready_agents: List[str] = []
    for agent in active_agents:
        if agent in scheduled:
            continue
        deps = dependencies.get(agent, [])
        if all(dep in executed for dep in deps):
            ready_agents.append(agent)

    if ready_agents:
        logger.info("Scheduling ready agents", agents=ready_agents)
        return {
            "scheduled_agents": ready_agents,
            "next_agent": ",".join(ready_agents),
        }

    # Inspect for deadlock scenarios
    unexecuted = [a for a in active_agents if a not in executed]
    in_flight = [a for a in scheduled if a not in executed]

    if unexecuted and not in_flight:
        logger.warn("DAG Deadlock detected! Routing directly to confidence engine to prevent freeze.", unexecuted=unexecuted)
        return {
            "next_agent": "confidence"
        }

    if not unexecuted:
        return {
            "next_agent": "confidence"
        }

    return {
        "next_agent": "wait"
    }


def route_next_agents(state: CopilotState) -> Union[List[str], str]:
    """Conditional edge router branching dynamically based on next_agent key."""
    next_agent = state.get("next_agent", "wait")
    if next_agent == "confidence":
        return "confidence"
    if next_agent == "wait" or not next_agent:
        return []

    node_routes = []
    for agent in next_agent.split(","):
        node_name = agent.strip().lower()
        if node_name == "factchecker":
            node_name = "fact_checker"
        node_routes.append(node_name)

    logger.info("Routing dynamic DAG edge routes", routes=node_routes)
    return node_routes




async def triage_node(state: CopilotState) -> Dict[str, Any]:
    """Runs triage category mapping."""
    context = AgentContext(
        ticket={"content": state["ticket_content"]},
        execution_plan=state["execution_plan"].dict(),
        retrieved_context=state["retrieved_context"],
        memory_context=state["memory_context"],
        tool_registry=registry,
        trace_id=state["trace_id"],
        logger=logger,
    )
    agent = TriageAgent(llm_gateway=llm_gateway)
    res = await agent.execute(context)
    return {
        "agent_results": {agent.name: res["output"]},
        "executed_agents": [agent.name],
        "audit_trail": [{"action": f"Executed agent {agent.name}", "cost": res["cost"]}],
    }


async def research_node(state: CopilotState) -> Dict[str, Any]:
    """Runs research text summarization."""
    context = AgentContext(
        ticket={"content": state["ticket_content"]},
        execution_plan=state["execution_plan"].dict(),
        retrieved_context=state["retrieved_context"],
        memory_context=state["memory_context"],
        tool_registry=registry,
        trace_id=state["trace_id"],
        logger=logger,
    )
    agent = ResearchAgent(llm_gateway=llm_gateway)
    res = await agent.execute(context)
    return {
        "agent_results": {agent.name: res["output"]},
        "executed_agents": [agent.name],
        "audit_trail": [{"action": f"Executed agent {agent.name}", "cost": res["cost"]}],
    }


async def policy_node(state: CopilotState) -> Dict[str, Any]:
    """Runs policy lookup verification."""
    context = AgentContext(
        ticket={"content": state["ticket_content"]},
        execution_plan=state["execution_plan"].dict(),
        retrieved_context=state["retrieved_context"],
        memory_context=state["memory_context"],
        tool_registry=registry,
        trace_id=state["trace_id"],
        logger=logger,
    )
    agent = PolicyAgent(llm_gateway=llm_gateway)
    res = await agent.execute(context)
    return {
        "agent_results": {agent.name: res["output"]},
        "executed_agents": [agent.name],
        "audit_trail": [{"action": f"Executed agent {agent.name}", "cost": res["cost"]}],
    }


async def draft_node(state: CopilotState) -> Dict[str, Any]:
    """Runs draft generator compiling inputs."""
    context = AgentContext(
        ticket={"content": state["ticket_content"], "agent_results": state["agent_results"]},
        execution_plan=state["execution_plan"].dict(),
        retrieved_context=state["retrieved_context"],
        memory_context=state["memory_context"],
        tool_registry=registry,
        trace_id=state["trace_id"],
        logger=logger,
    )
    agent = DraftAgent(llm_gateway=llm_gateway)
    res = await agent.execute(context)
    return {
        "draft_response": res["output"],
        "executed_agents": [agent.name],
        "audit_trail": [{"action": "Formulated response draft", "cost": res["cost"]}],
    }


async def fact_checker_node(state: CopilotState) -> Dict[str, Any]:
    """Runs fact checker verification."""
    context = AgentContext(
        ticket={"content": state["ticket_content"], "draft_response": state["draft_response"]},
        execution_plan=state["execution_plan"].dict(),
        retrieved_context=state["retrieved_context"],
        memory_context=state["memory_context"],
        tool_registry=registry,
        trace_id=state["trace_id"],
        logger=logger,
    )
    agent = FactCheckerAgent(llm_gateway=llm_gateway)
    res = await agent.execute(context)
    import json
    parsed = json.loads(res["output"])
    return {
        "validation_results": {agent.name: parsed},
        "executed_agents": [agent.name],
        "audit_trail": [{"action": f"Executed verification {agent.name}", "cost": res["cost"]}],
    }


async def confidence_node(state: CopilotState) -> Dict[str, Any]:
    """Runs confidence scoring calculations."""
    engine = ConfidenceEngine()
    fc_results = state["validation_results"].get("FactChecker", {})
    scores = engine.compute_score(
        draft=state["draft_response"],
        sources=state["retrieved_context"],
        fact_checker_output=fc_results,
    )
    return {
        "confidence_scores": scores,
        "audit_trail": [{"action": "Computed overall confidence scores", "scores": scores}],
    }


async def human_review_node(state: CopilotState) -> Dict[str, Any]:
    """Suspends graph execution to request human input."""
    # Emit requested event
    event_bus.publish(
        SystemEvent(
            event_type="HumanReviewRequested",
            trace_id=state["trace_id"],
            payload={"ticket_id": state["ticket_id"]},
        )
    )
    # Interrupt step occurs here - user resumes by passing values
    from langgraph.errors import GraphInterrupt
    # Standard LangGraph manual trigger interruption wrapper
    raise GraphInterrupt("Human review required for draft response.")


async def execute_node(state: CopilotState) -> Dict[str, Any]:
    """Finalizes response execution logging completed trace events."""
    event_bus.publish(
        SystemEvent(
            event_type="HumanReviewCompleted",
            trace_id=state["trace_id"],
            payload={"ticket_id": state["ticket_id"], "decision": state.get("review_decision", "approved")},
        )
    )
    return {
        "audit_trail": [{"action": "Final response dispatched", "decision": state.get("review_decision")}]
    }


def build_orchestrator_graph() -> StateGraph:
    """Builds and compiles the complete multi-agent workflow graph."""
    workflow = StateGraph(CopilotState)

    # 1. Add all graph nodes
    workflow.add_node("planner", planner_node)
    workflow.add_node("coordinator", coordinator_node)
    workflow.add_node("triage", triage_node)
    workflow.add_node("research", research_node)
    workflow.add_node("policy", policy_node)
    workflow.add_node("draft", draft_node)
    workflow.add_node("fact_checker", fact_checker_node)
    workflow.add_node("confidence", confidence_node)
    workflow.add_node("human_review", human_review_node)
    workflow.add_node("execute", execute_node)

    # 2. Configure edges
    workflow.add_edge(START, "planner")
    workflow.add_edge("planner", "coordinator")

    # Coordinator dynamic routing
    workflow.add_conditional_edges(
        "coordinator",
        route_next_agents,
        path_map={
            "triage": "triage",
            "research": "research",
            "policy": "policy",
            "draft": "draft",
            "fact_checker": "fact_checker",
            "confidence": "confidence",
        }
    )

    # Fan-in edges back to coordinator
    workflow.add_edge("triage", "coordinator")
    workflow.add_edge("research", "coordinator")
    workflow.add_edge("policy", "coordinator")
    workflow.add_edge("draft", "coordinator")
    workflow.add_edge("fact_checker", "coordinator")

    # Final straight pipeline
    workflow.add_edge("confidence", "human_review")
    workflow.add_edge("human_review", "execute")
    workflow.add_edge("execute", END)

    return workflow

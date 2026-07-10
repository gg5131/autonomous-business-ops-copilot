"""Decision path tracing recording agent reasoning chains, retrieval references, and scoring paths."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.observability.logging import get_logger

logger = get_logger(__name__)


@dataclass
class TraceRecord:
    """Dataclass holding explainability audit information for execution paths."""

    trace_id: str
    steps: List[Dict[str, Any]] = field(default_factory=list)
    citations: List[Dict[str, Any]] = field(default_factory=list)
    scores: Dict[str, float] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class ExplainabilityTracer:
    """Collects and format decision-path details to render on the reviewer dashboard."""

    def __init__(self) -> None:
        self._traces: Dict[str, TraceRecord] = {}

    def start_trace(self, trace_id: str) -> None:
        """Initialize a new trace record."""
        self._traces[trace_id] = TraceRecord(trace_id=trace_id)
        logger.info("Decision path tracing started", trace_id=trace_id)

    def record_step(self, trace_id: str, agent_name: str, output: str, metrics: Dict[str, Any]) -> None:
        """Append an execution step outcome to the trace track."""
        if trace_id not in self._traces:
            self.start_trace(trace_id)

        self._traces[trace_id].steps.append(
            {
                "agent": agent_name,
                "output": output,
                "timestamp": datetime.utcnow().isoformat(),
                **metrics,
            }
        )
        logger.info("Agent execution recorded in trace path", trace_id=trace_id, agent=agent_name)

    def record_citations(self, trace_id: str, citations: List[Dict[str, Any]]) -> None:
        """Logs retrieved source documents used for citations check."""
        if trace_id not in self._traces:
            self.start_trace(trace_id)
        self._traces[trace_id].citations = citations

    def record_scores(self, trace_id: str, scores: Dict[str, float]) -> None:
        """Saves confidence scores of the run."""
        if trace_id not in self._traces:
            self.start_trace(trace_id)
        self._traces[trace_id].scores = scores

    def get_explanation(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """Return formatted markdown or structured payload explaining agent decisions."""
        trace = self._traces.get(trace_id)
        if not trace:
            return None

        # Build clear explanation markdown summary
        markdown_lines = [
            f"# Decision Explanation for Trace: `{trace_id}`",
            f"Executed at: `{trace.timestamp}`",
            "",
            "## 🤖 Execution Agent Path",
        ]

        for i, step in enumerate(trace.steps, 1):
            markdown_lines.append(
                f"{i}. **{step['agent']} Agent** (latency: `{step.get('latency_ms', 0.0):.1f}ms`, cost: `${step.get('cost_usd', 0.0):.5f}`)"
            )

        if trace.scores:
            markdown_lines.append("\n## 📊 Confidence Scoring Analysis")
            for metric, val in trace.scores.items():
                markdown_lines.append(f"- **{metric.replace('_', ' ').title()}**: `{val:.1f}%`")

        if trace.citations:
            markdown_lines.append("\n## 📚 Sources & Citations")
            for doc in trace.citations:
                markdown_lines.append(f"- [{doc.get('id')}] Content: *{doc.get('content', '')[:100]}...*")

        return {
            "trace_id": trace_id,
            "explanation_markdown": "\n".join(markdown_lines),
            "raw_record": trace,
        }


# Global tracer instance
tracer = ExplainabilityTracer()

"""SQLAlchemy 2.0 declarative database models mapped to the domain schema."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, List, Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator


# Custom JSON type fallback for SQLite vs Postgres
class SafeJSON(TypeDecorator):
    """Custom JSON type that falls back to SQLAlchemy String/JSON on SQLite and JSONB on PostgreSQL."""

    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect: Any) -> Any:
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        else:
            from sqlalchemy.types import JSON

            return dialect.type_descriptor(JSON())


class Base(DeclarativeBase):
    """SQLAlchemy base class for all database models."""


class User(Base):
    """Represents an internal reviewer or supervisor user."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    permissions: Mapped[Optional[Any]] = mapped_column(SafeJSON, nullable=True)

    decisions: Mapped[List[ReviewDecision]] = relationship("ReviewDecision", back_populates="reviewer")


class Ticket(Base):
    """Represents a customer-submitted support request or task."""

    __tablename__ = "tickets"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    priority: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="open", nullable=False)
    customer_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    metadata_json: Mapped[Optional[Any]] = mapped_column(SafeJSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    runs: Mapped[List[ProcessingRun]] = relationship("ProcessingRun", back_populates="ticket")


class ProcessingRun(Base):
    """Represents a execution run of the multi-agent system on a ticket."""

    __tablename__ = "processing_runs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    ticket_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("tickets.id"), nullable=False)
    thread_id: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    total_latency_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_cost_usd: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    ticket: Mapped[Ticket] = relationship("Ticket", back_populates="runs")
    plan: Mapped[Optional[ExecutionPlan]] = relationship("ExecutionPlan", back_populates="run", uselist=False)
    executions: Mapped[List[AgentExecution]] = relationship("AgentExecution", back_populates="run")
    drafts: Mapped[List[DraftResponse]] = relationship("DraftResponse", back_populates="run")
    confidence_score: Mapped[Optional[ConfidenceScore]] = relationship("ConfidenceScore", back_populates="run", uselist=False)
    audit_entries: Mapped[List[AuditEntry]] = relationship("AuditEntry", back_populates="run")


class AgentExecution(Base):
    """Represents the execution records of individual agents during a processing run."""

    __tablename__ = "agent_executions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("processing_runs.id"), nullable=False)
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    input_data: Mapped[Optional[Any]] = mapped_column(SafeJSON, nullable=True)
    output_data: Mapped[Optional[Any]] = mapped_column(SafeJSON, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    executed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    run: Mapped[ProcessingRun] = relationship("ProcessingRun", back_populates="executions")


class ExecutionPlan(Base):
    """Stores the execution plan generated by the Planner Agent."""

    __tablename__ = "execution_plans"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("processing_runs.id"), nullable=False)
    planned_agents: Mapped[Any] = mapped_column(SafeJSON, nullable=False)
    parallel_groups: Mapped[Optional[Any]] = mapped_column(SafeJSON, nullable=True)
    reasoning: Mapped[str] = mapped_column(Text, nullable=False)

    run: Mapped[ProcessingRun] = relationship("ProcessingRun", back_populates="plan")


class DraftResponse(Base):
    """Represents a draft response produced by the Draft Agent."""

    __tablename__ = "draft_responses"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("processing_runs.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    citations: Mapped[Optional[Any]] = mapped_column(SafeJSON, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    version: Mapped[str] = mapped_column(String(50), default="1.0", nullable=False)

    run: Mapped[ProcessingRun] = relationship("ProcessingRun", back_populates="drafts")
    decisions: Mapped[List[ReviewDecision]] = relationship("ReviewDecision", back_populates="draft")


class ReviewDecision(Base):
    """Stores human-in-the-loop decisions (approve, edit, reject) on draft responses."""

    __tablename__ = "review_decisions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    draft_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("draft_responses.id"), nullable=False)
    reviewer_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"), nullable=False)
    decision: Mapped[str] = mapped_column(String(50), nullable=False)  # approved, edited, rejected
    edited_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    decided_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    draft: Mapped[DraftResponse] = relationship("DraftResponse", back_populates="decisions")
    reviewer: Mapped[User] = relationship("User", back_populates="decisions")


class ConfidenceScore(Base):
    """Represents the decomposed metric confidence scores computed by the confidence engine."""

    __tablename__ = "confidence_scores"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("processing_runs.id"), nullable=False)
    overall: Mapped[float] = mapped_column(Float, nullable=False)
    groundedness: Mapped[float] = mapped_column(Float, nullable=False)
    citation_coverage: Mapped[float] = mapped_column(Float, nullable=False)
    hallucination_risk: Mapped[float] = mapped_column(Float, nullable=False)
    policy_risk: Mapped[float] = mapped_column(Float, nullable=False)
    validation_pass_rate: Mapped[float] = mapped_column(Float, nullable=False)

    run: Mapped[ProcessingRun] = relationship("ProcessingRun", back_populates="confidence_score")


class AuditEntry(Base):
    """A log of immutable operations / system traces stored in relational database."""

    __tablename__ = "audit_entries"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    run_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("processing_runs.id"), nullable=True)
    event_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    agent_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    event_data: Mapped[Any] = mapped_column(SafeJSON, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    run: Mapped[Optional[ProcessingRun]] = relationship("ProcessingRun", back_populates="audit_entries")

"""SQLAlchemy Models for KALI Sentinel Audit & Persistence Layer.

Tables:
- security_requests: Audit of incoming security analysis requests.
- decisions: Strands Decider 2B typed decisions, confidence, and latency.
- tool_executions: Defensive tool execution results and status.
- agent_memory: Context & memory records with pgvector support.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON, Text as TextType, TypeDecorator

from OpenDEMON.database.base import Base

try:
    from pgvector.sqlalchemy import Vector
    HAS_PGVECTOR = True
except ImportError:
    Vector = None
    HAS_PGVECTOR = False


def utcnow() -> datetime:
    """Return current UTC timestamp with timezone."""
    return datetime.now(timezone.utc)


def uuid_gen() -> str:
    """Generate string UUID4."""
    return str(uuid.uuid4())


class SafeVector(TypeDecorator):
    """Dialect-adaptive vector type.
    
    Uses pgvector Vector(dim) when on PostgreSQL with the extension installed,
    and cleanly falls back to JSON on SQLite/in-memory test databases.
    """

    impl = TextType
    cache_ok = True

    def __init__(self, dim: int = 768, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.dim = dim

    def load_dialect_impl(self, dialect: Any) -> Any:
        if dialect.name == "postgresql" and Vector is not None:
            return dialect.type_descriptor(Vector(self.dim))
        return dialect.type_descriptor(JSON())


class SecurityRequestRecord(Base):
    """Table 1: security_requests
    
    Audit record for incoming security tasks submitted to KALI Sentinel.
    """

    __tablename__ = "security_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_gen)
    session_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    request_text: Mapped[str] = mapped_column(Text, nullable=False)
    target: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    authorized: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        server_default=func.now(),
        index=True,
        nullable=False,
    )

    # Relationships
    decisions: Mapped[List[DecisionRecord]] = relationship(
        "DecisionRecord",
        back_populates="request",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    tool_executions: Mapped[List[ToolExecutionRecord]] = relationship(
        "ToolExecutionRecord",
        back_populates="request",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "request_text": self.request_text,
            "target": self.target,
            "authorized": self.authorized,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "decisions": [d.to_dict() for d in self.decisions] if self.decisions else [],
            "tool_executions": [t.to_dict() for t in self.tool_executions] if self.tool_executions else [],
        }


class DecisionRecord(Base):
    """Table 2: decisions
    
    Audit record of typed tool decisions emitted by Strands Decider 2B.
    """

    __tablename__ = "decisions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_gen)
    request_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("security_requests.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    decision: Mapped[str] = mapped_column(String(64), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    latency_ms: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        server_default=func.now(),
        index=True,
        nullable=False,
    )

    # Relationship back to security request
    request: Mapped[SecurityRequestRecord] = relationship(
        "SecurityRequestRecord",
        back_populates="decisions",
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "request_id": self.request_id,
            "decision": self.decision,
            "confidence": self.confidence,
            "latency_ms": self.latency_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ToolExecutionRecord(Base):
    """Table 3: tool_executions
    
    Audit record of defensive security tools executed by safe adapters.
    """

    __tablename__ = "tool_executions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_gen)
    request_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("security_requests.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    tool_name: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    result: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    execution_latency_ms: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        server_default=func.now(),
        index=True,
        nullable=False,
    )

    # Relationship back to security request
    request: Mapped[SecurityRequestRecord] = relationship(
        "SecurityRequestRecord",
        back_populates="tool_executions",
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "request_id": self.request_id,
            "tool_name": self.tool_name,
            "status": self.status,
            "result": self.result,
            "execution_latency_ms": self.execution_latency_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AgentMemoryRecord(Base):
    """Table 4: agent_memory
    
    Context & Memory store with pgvector embedding support for security sessions.
    """

    __tablename__ = "agent_memory"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_gen)
    session_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[Optional[Any]] = mapped_column(SafeVector(768), nullable=True)
    metadata_json: Mapped[Dict[str, Any]] = mapped_column("metadata", JSON, default=dict, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        server_default=func.now(),
        index=True,
        nullable=False,
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "content": self.content,
            "metadata": self.metadata_json,
            "has_embedding": self.embedding is not None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

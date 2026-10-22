"""Repository Layer for KALI Sentinel Audit and Persistence.

Provides clean, database-independent methods for recording:
- Security analysis requests
- Strands Decider 2B typed decisions
- Tool execution results
- Agent memory and pgvector embeddings

Includes safe in-memory fallback for local development and sensitive data scrubbing.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
import asyncio
from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
import uuid

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from kali_sentinel.database.models import (
    AgentMemoryRecord,
    DecisionRecord,
    SecurityRequestRecord,
    ToolExecutionRecord,
    uuid_gen,
)
from kali_sentinel.database.session import get_db_session, is_database_configured

logger = logging.getLogger(__name__)

# Keys that must never be persisted in plain text
SENSITIVE_FIELD_NAMES = {
    "aws_access_key_id",
    "aws_secret_access_key",
    "aws_session_token",
    "api_key",
    "password",
    "token",
    "secret",
    "private_key",
    "credentials",
    "authorization",
    "jwt_secret",
    "access_token",
}


def sanitize_audit_data(data: Any) -> Any:
    """Recursively scrub credentials, tokens, and secret keys before storage."""
    if isinstance(data, dict):
        cleaned: Dict[str, Any] = {}
        for k, v in data.items():
            if any(s in str(k).lower() for s in SENSITIVE_FIELD_NAMES):
                cleaned[str(k)] = "[REDACTED]"
            else:
                cleaned[str(k)] = sanitize_audit_data(v)
        return cleaned
    elif isinstance(data, list):
        return [sanitize_audit_data(item) for item in data]
    return data


class SentinelRepositoryInterface(ABC):
    """Abstract interface defining required repository methods."""

    @abstractmethod
    async def create_security_request(
        self,
        request_text: str,
        target: Optional[str] = None,
        authorized: bool = True,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new security request audit record."""
        raise NotImplementedError

    @abstractmethod
    async def record_decision(
        self,
        request_id: str,
        decision: str,
        confidence: float,
        latency_ms: float,
    ) -> Dict[str, Any]:
        """Record Strands Decider 2B tool selection decision."""
        raise NotImplementedError

    @abstractmethod
    async def record_tool_execution(
        self,
        request_id: str,
        tool_name: str,
        status: str,
        result: Dict[str, Any],
        execution_latency_ms: float,
    ) -> Dict[str, Any]:
        """Record defensive tool execution status and findings."""
        raise NotImplementedError

    @abstractmethod
    async def get_request_history(
        self,
        limit: int = 50,
        session_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve recent security request audit records."""
        raise NotImplementedError

    @abstractmethod
    async def get_decision_history(
        self,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Retrieve recent Decider 2B decisions."""
        raise NotImplementedError

    @abstractmethod
    async def save_memory(
        self,
        session_id: str,
        content: str,
        embedding: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Persist memory snippet for agent context."""
        raise NotImplementedError

    @abstractmethod
    async def search_memory(
        self,
        session_id: str,
        query: Optional[str] = None,
        embedding: Optional[List[float]] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Search memory snippets for a given session."""
        raise NotImplementedError


class SQLAlchemySentinelRepository(SentinelRepositoryInterface):
    """PostgreSQL / SQLite implementation using SQLAlchemy 2.0 AsyncSession."""

    def __init__(self, session_override: Optional[AsyncSession] = None) -> None:
        self._session_override = session_override

    async def create_security_request(
        self,
        request_text: str,
        target: Optional[str] = None,
        authorized: bool = True,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        cleaned_text = sanitize_audit_data(request_text)
        record = SecurityRequestRecord(
            id=uuid_gen(),
            session_id=session_id,
            request_text=str(cleaned_text),
            target=target,
            authorized=bool(authorized),
        )

        # Mirror to in-memory cache
        await _GLOBAL_IN_MEMORY_REPO.create_security_request(
            request_text=request_text,
            target=target,
            authorized=authorized,
            session_id=session_id,
        )

        if self._session_override:
            self._session_override.add(record)
            await self._session_override.commit()
            await self._session_override.refresh(record)
            return record.to_dict()

        try:
            async with get_db_session() as session:
                if session is None:
                    return record.to_dict()
                session.add(record)
                await session.commit()
                await session.refresh(record)
                return record.to_dict()
        except Exception as exc:
            logger.warning("Database insert security_request failed (%s); using in-memory store.", exc)
            return record.to_dict()

    async def record_decision(
        self,
        request_id: str,
        decision: str,
        confidence: float,
        latency_ms: float,
    ) -> Dict[str, Any]:
        record = DecisionRecord(
            id=uuid_gen(),
            request_id=request_id,
            decision=str(decision).upper(),
            confidence=float(confidence),
            latency_ms=float(latency_ms),
        )

        # Mirror to in-memory cache
        await _GLOBAL_IN_MEMORY_REPO.record_decision(
            request_id=request_id,
            decision=decision,
            confidence=confidence,
            latency_ms=latency_ms,
        )

        if self._session_override:
            self._session_override.add(record)
            await self._session_override.commit()
            await self._session_override.refresh(record)
            return record.to_dict()

        try:
            async with get_db_session() as session:
                if session is None:
                    return record.to_dict()
                session.add(record)
                await session.commit()
                await session.refresh(record)
                return record.to_dict()
        except Exception as exc:
            logger.warning("Database insert decision failed (%s); using in-memory store.", exc)
            return record.to_dict()

    async def record_tool_execution(
        self,
        request_id: str,
        tool_name: str,
        status: str,
        result: Dict[str, Any],
        execution_latency_ms: float,
    ) -> Dict[str, Any]:
        sanitized_result = sanitize_audit_data(result or {})
        record = ToolExecutionRecord(
            id=uuid_gen(),
            request_id=request_id,
            tool_name=str(tool_name),
            status=str(status).upper(),
            result=sanitized_result,
            execution_latency_ms=float(execution_latency_ms),
        )

        # Mirror to in-memory cache
        await _GLOBAL_IN_MEMORY_REPO.record_tool_execution(
            request_id=request_id,
            tool_name=tool_name,
            status=status,
            result=result,
            execution_latency_ms=execution_latency_ms,
        )

        if self._session_override:
            self._session_override.add(record)
            await self._session_override.commit()
            await self._session_override.refresh(record)
            return record.to_dict()

        try:
            async with get_db_session() as session:
                if session is None:
                    return record.to_dict()
                session.add(record)
                await session.commit()
                await session.refresh(record)
                return record.to_dict()
        except Exception as exc:
            logger.warning("Database insert tool_execution failed (%s); using in-memory store.", exc)
            return record.to_dict()

    async def get_request_history(
        self,
        limit: int = 50,
        session_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        stmt = select(SecurityRequestRecord).order_by(desc(SecurityRequestRecord.created_at)).limit(limit)
        if session_id:
            stmt = stmt.where(SecurityRequestRecord.session_id == session_id)

        if self._session_override:
            res = await self._session_override.execute(stmt)
            return [r.to_dict() for r in res.scalars().all()]

        try:
            async with get_db_session() as session:
                if session is None:
                    return await _GLOBAL_IN_MEMORY_REPO.get_request_history(limit=limit, session_id=session_id)
                res = await session.execute(stmt)
                return [r.to_dict() for r in res.scalars().all()]
        except Exception as exc:
            logger.warning("Database get_request_history query failed (%s); using in-memory store.", exc)
            return await _GLOBAL_IN_MEMORY_REPO.get_request_history(limit=limit, session_id=session_id)

    async def get_decision_history(
        self,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        stmt = select(DecisionRecord).order_by(desc(DecisionRecord.created_at)).limit(limit)

        if self._session_override:
            res = await self._session_override.execute(stmt)
            return [r.to_dict() for r in res.scalars().all()]

        try:
            async with get_db_session() as session:
                if session is None:
                    return await _GLOBAL_IN_MEMORY_REPO.get_decision_history(limit=limit)
                res = await session.execute(stmt)
                return [r.to_dict() for r in res.scalars().all()]
        except Exception as exc:
            logger.warning("Database get_decision_history query failed (%s); using in-memory store.", exc)
            return await _GLOBAL_IN_MEMORY_REPO.get_decision_history(limit=limit)

    async def save_memory(
        self,
        session_id: str,
        content: str,
        embedding: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        sanitized_meta = sanitize_audit_data(metadata or {})
        record = AgentMemoryRecord(
            id=uuid_gen(),
            session_id=str(session_id),
            content=str(content),
            embedding=embedding,
            metadata_json=sanitized_meta,
        )

        if self._session_override:
            self._session_override.add(record)
            await self._session_override.commit()
            await self._session_override.refresh(record)
            return record.to_dict()

        async with get_db_session() as session:
            if session is None:
                raise RuntimeError("No database session available.")
            session.add(record)
            await session.commit()
            await session.refresh(record)
            return record.to_dict()

    async def search_memory(
        self,
        session_id: str,
        query: Optional[str] = None,
        embedding: Optional[List[float]] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        stmt = select(AgentMemoryRecord).where(AgentMemoryRecord.session_id == session_id)

        # If pgvector embedding is provided and supported
        if embedding is not None and hasattr(AgentMemoryRecord.embedding, "cosine_distance"):
            try:
                stmt = stmt.order_by(AgentMemoryRecord.embedding.cosine_distance(embedding))
            except Exception:
                stmt = stmt.order_by(desc(AgentMemoryRecord.created_at))
        elif query:
            stmt = stmt.where(AgentMemoryRecord.content.ilike(f"%{query}%")).order_by(desc(AgentMemoryRecord.created_at))
        else:
            stmt = stmt.order_by(desc(AgentMemoryRecord.created_at))

        stmt = stmt.limit(limit)

        if self._session_override:
            res = await self._session_override.execute(stmt)
            return [r.to_dict() for r in res.scalars().all()]

        async with get_db_session() as session:
            if session is None:
                return []
            res = await session.execute(stmt)
            return [r.to_dict() for r in res.scalars().all()]


class InMemorySentinelRepository(SentinelRepositoryInterface):
    """In-memory audit and memory store for local development without PostgreSQL."""

    def __init__(self) -> None:
        self._requests: List[Dict[str, Any]] = []
        self._decisions: List[Dict[str, Any]] = []
        self._tool_executions: List[Dict[str, Any]] = []
        self._memories: List[Dict[str, Any]] = []
        self._lock = asyncio.Lock()

    async def create_security_request(
        self,
        request_text: str,
        target: Optional[str] = None,
        authorized: bool = True,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        async with self._lock:
            rec = {
                "id": str(uuid.uuid4()),
                "session_id": session_id,
                "request_text": str(sanitize_audit_data(request_text)),
                "target": target,
                "authorized": bool(authorized),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "decisions": [],
                "tool_executions": [],
            }
            self._requests.append(rec)
            return dict(rec)

    async def record_decision(
        self,
        request_id: str,
        decision: str,
        confidence: float,
        latency_ms: float,
    ) -> Dict[str, Any]:
        async with self._lock:
            rec = {
                "id": str(uuid.uuid4()),
                "request_id": request_id,
                "decision": str(decision).upper(),
                "confidence": float(confidence),
                "latency_ms": float(latency_ms),
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            self._decisions.append(rec)

            # Link into request object if present
            for req in self._requests:
                if req["id"] == request_id:
                    req["decisions"].append(rec)
                    break
            return dict(rec)

    async def record_tool_execution(
        self,
        request_id: str,
        tool_name: str,
        status: str,
        result: Dict[str, Any],
        execution_latency_ms: float,
    ) -> Dict[str, Any]:
        async with self._lock:
            rec = {
                "id": str(uuid.uuid4()),
                "request_id": request_id,
                "tool_name": str(tool_name),
                "status": str(status).upper(),
                "result": sanitize_audit_data(result or {}),
                "execution_latency_ms": float(execution_latency_ms),
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            self._tool_executions.append(rec)

            for req in self._requests:
                if req["id"] == request_id:
                    req["tool_executions"].append(rec)
                    break
            return dict(rec)

    async def get_request_history(
        self,
        limit: int = 50,
        session_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        async with self._lock:
            items = list(self._requests)
            if session_id:
                items = [r for r in items if r.get("session_id") == session_id]
            items.reverse()
            return items[:limit]

    async def get_decision_history(
        self,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        async with self._lock:
            items = list(self._decisions)
            items.reverse()
            return items[:limit]

    async def save_memory(
        self,
        session_id: str,
        content: str,
        embedding: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        async with self._lock:
            rec = {
                "id": str(uuid.uuid4()),
                "session_id": str(session_id),
                "content": str(content),
                "has_embedding": embedding is not None,
                "embedding": embedding,
                "metadata": sanitize_audit_data(metadata or {}),
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            self._memories.append(rec)
            return dict(rec)

    async def search_memory(
        self,
        session_id: str,
        query: Optional[str] = None,
        embedding: Optional[List[float]] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        async with self._lock:
            matches = [m for m in self._memories if m["session_id"] == session_id]
            if query:
                q_l = query.lower()
                matches = [m for m in matches if q_l in m["content"].lower()]
            matches.reverse()
            return matches[:limit]


# Global shared in-memory instance for fallback
_GLOBAL_IN_MEMORY_REPO = InMemorySentinelRepository()
_REPO_OVERRIDE: Optional[SentinelRepositoryInterface] = None


def set_repository_override(repo: Optional[SentinelRepositoryInterface]) -> None:
    """Set custom repository instance (e.g. for testing)."""
    global _REPO_OVERRIDE
    _REPO_OVERRIDE = repo


def get_sentinel_repository() -> SentinelRepositoryInterface:
    """Factory returning active SQLAlchemy or InMemory repository."""
    global _REPO_OVERRIDE
    if _REPO_OVERRIDE is not None:
        return _REPO_OVERRIDE

    if is_database_configured():
        return SQLAlchemySentinelRepository()

    return _GLOBAL_IN_MEMORY_REPO

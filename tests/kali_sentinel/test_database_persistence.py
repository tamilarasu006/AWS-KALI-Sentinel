"""Tests for KALI Sentinel Database Persistence & Audit Layer.

Covers:
1. Creating a security request
2. Recording a decision
3. Recording tool execution
4. Retrieving decision and request history
5. Database-unavailable fallback
6. No secret values being persisted (scrubbing AWS keys/passwords)
7. API analysis creates the expected audit records
8. Agent memory save and search
9. SQLAlchemy repository integration with real async database engine
"""

import asyncio
from typing import AsyncIterator
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from OpenDEMON.database.base import Base
from kali_sentinel.database import (
    AgentMemoryRecord,
    DecisionRecord,
    InMemorySentinelRepository,
    SQLAlchemySentinelRepository,
    SecurityRequestRecord,
    ToolExecutionRecord,
    check_db_health,
    get_sentinel_repository,
    sanitize_audit_data,
    set_engine_for_testing,
    set_repository_override,
)
from kali_sentinel.server.routes import create_sentinel_app


@pytest_asyncio.fixture
async def sqlite_engine():
    """Create in-memory SQLite async engine with all KALI Sentinel tables."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def sqlite_session(sqlite_engine) -> AsyncIterator[AsyncSession]:
    """Yield an active async session on the test SQLite database."""
    factory = async_sessionmaker(bind=sqlite_engine, expire_on_commit=False)
    async with factory() as session:
        yield session


# ---------------------------------------------------------------------------
# 1. Creating a Security Request
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_security_request():
    """Verify security request creation in repository with proper fields."""
    repo = InMemorySentinelRepository()
    req = await repo.create_security_request(
        request_text="Check open ports on my authorized lab server.",
        target="lab.local",
        authorized=True,
        session_id="session-123",
    )

    assert req["id"] is not None
    assert len(req["id"]) > 10
    assert req["request_text"] == "Check open ports on my authorized lab server."
    assert req["target"] == "lab.local"
    assert req["authorized"] is True
    assert req["session_id"] == "session-123"
    assert req["created_at"] is not None


# ---------------------------------------------------------------------------
# 2. Recording a Decision
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_record_decision():
    """Verify recording a typed decision linked to a request."""
    repo = InMemorySentinelRepository()
    req = await repo.create_security_request("Scan ports", target="localhost", authorized=True)

    dec = await repo.record_decision(
        request_id=req["id"],
        decision="PORT_SCAN",
        confidence=0.965,
        latency_ms=45.2,
    )

    assert dec["id"] is not None
    assert dec["request_id"] == req["id"]
    assert dec["decision"] == "PORT_SCAN"
    assert dec["confidence"] == 0.965
    assert dec["latency_ms"] == 45.2
    assert dec["created_at"] is not None


# ---------------------------------------------------------------------------
# 3. Recording Tool Execution
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_record_tool_execution():
    """Verify recording tool execution results and status."""
    repo = InMemorySentinelRepository()
    req = await repo.create_security_request("Audit DNS", target="test.local", authorized=True)

    tool_res = {
        "domain": "test.local",
        "records": {"A": ["127.0.0.1"], "SPF": "v=spf1 -all"},
    }
    exec_record = await repo.record_tool_execution(
        request_id=req["id"],
        tool_name="dns_check_tool",
        status="COMPLETED",
        result=tool_res,
        execution_latency_ms=125.4,
    )

    assert exec_record["id"] is not None
    assert exec_record["request_id"] == req["id"]
    assert exec_record["tool_name"] == "dns_check_tool"
    assert exec_record["status"] == "COMPLETED"
    assert exec_record["result"] == tool_res
    assert exec_record["execution_latency_ms"] == 125.4


# ---------------------------------------------------------------------------
# 4. Retrieving Decision and Request History
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_retrieve_decision_and_request_history():
    """Verify historical query retrieval for requests and decisions."""
    repo = InMemorySentinelRepository()

    # Create 3 requests and decisions
    for i in range(3):
        r = await repo.create_security_request(f"Task {i}", target=f"target-{i}.local")
        await repo.record_decision(r["id"], decision="PORT_SCAN", confidence=0.85 + i * 0.05, latency_ms=10.0 + i)

    req_history = await repo.get_request_history(limit=10)
    assert len(req_history) == 3
    # Most recent first
    assert req_history[0]["request_text"] == "Task 2"

    dec_history = await repo.get_decision_history(limit=10)
    assert len(dec_history) == 3
    assert dec_history[0]["decision"] == "PORT_SCAN"


# ---------------------------------------------------------------------------
# 5. Database-Unavailable Fallback
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_database_unavailable_fallback():
    """Verify health check returns clean offline fallback status when unconfigured."""
    set_repository_override(None)
    health = await check_db_health()

    assert "status" in health
    assert "connected" in health
    # Does not crash or raise uncaught exceptions
    assert isinstance(health["connected"], bool)


# ---------------------------------------------------------------------------
# 6. No Secret Values Being Persisted (Sanitization)
# ---------------------------------------------------------------------------

def test_no_secret_values_persisted():
    """Verify that credentials, tokens, and secrets are scrubbed before storage."""
    payload_with_secrets = {
        "user_request": "Audit server with key",
        "aws_access_key_id": "AKIAIOSFODNN7EXAMPLE",
        "aws_secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        "api_key": "secret-api-token-12345",
        "nested": {
            "password": "SuperSecretPassword123!",
            "public_metric": 42,
        },
    }

    sanitized = sanitize_audit_data(payload_with_secrets)

    assert sanitized["aws_access_key_id"] == "[REDACTED]"
    assert sanitized["aws_secret_access_key"] == "[REDACTED]"
    assert sanitized["api_key"] == "[REDACTED]"
    assert sanitized["nested"]["password"] == "[REDACTED]"
    assert sanitized["nested"]["public_metric"] == 42
    assert sanitized["user_request"] == "Audit server with key"


# ---------------------------------------------------------------------------
# 7. API Analysis Creates Expected Audit Records
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_api_analysis_creates_audit_records():
    """Verify POST /v1/sentinel/analyze creates audit records in repository."""
    test_repo = InMemorySentinelRepository()
    set_repository_override(test_repo)

    app = create_sentinel_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "request": "Check open ports on my authorized lab server.",
            "authorized": True,
            "session_id": "session-test-audit",
        }
        resp = await client.post("/v1/sentinel/analyze", json=payload)
        assert resp.status_code == 200
        data = resp.json()

        assert data["decision"] == "PORT_SCAN"
        assert data["audit_request_id"] is not None
        assert data["persistence_status"] == "persisted"

        # Verify audit records in repository
        requests = await test_repo.get_request_history(session_id="session-test-audit")
        assert len(requests) == 1
        assert requests[0]["id"] == data["audit_request_id"]
        assert requests[0]["authorized"] is True

        decisions = await test_repo.get_decision_history()
        assert len(decisions) >= 1
        assert decisions[0]["decision"] == "PORT_SCAN"

    set_repository_override(None)


# ---------------------------------------------------------------------------
# 8. Agent Memory Save and Search
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_agent_memory_save_and_search():
    """Verify agent_memory storage and retrieval."""
    repo = InMemorySentinelRepository()

    saved = await repo.save_memory(
        session_id="session-mem-1",
        content="Lab host 127.0.0.1 confirmed as primary development target.",
        metadata={"category": "scope", "auth_level": "admin"},
    )

    assert saved["id"] is not None
    assert saved["session_id"] == "session-mem-1"
    assert "Lab host" in saved["content"]
    assert saved["metadata"]["category"] == "scope"

    results = await repo.search_memory(session_id="session-mem-1", query="primary")
    assert len(results) == 1
    assert results[0]["id"] == saved["id"]

    empty_results = await repo.search_memory(session_id="session-mem-1", query="nonexistent")
    assert len(empty_results) == 0


# ---------------------------------------------------------------------------
# 9. SQLAlchemy Repository with Real Async SQLite Database
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_sqlalchemy_repository_with_sqlite(sqlite_session):
    """Verify SQLAlchemySentinelRepository executes against real database."""
    repo = SQLAlchemySentinelRepository(session_override=sqlite_session)

    # 1. Create Request
    req = await repo.create_security_request(
        request_text="Audit web application security headers.",
        target="http://localhost:8080",
        authorized=True,
        session_id="session-sql-1",
    )
    assert req["id"] is not None

    # 2. Record Decision
    dec = await repo.record_decision(
        request_id=req["id"],
        decision="WEB_SCAN",
        confidence=0.88,
        latency_ms=12.5,
    )
    assert dec["decision"] == "WEB_SCAN"

    # 3. Record Execution
    exec_rec = await repo.record_tool_execution(
        request_id=req["id"],
        tool_name="web_scan_tool",
        status="COMPLETED",
        result={"csp": "strict-dynamic", "hsts": True},
        execution_latency_ms=85.0,
    )
    assert exec_rec["status"] == "COMPLETED"

    # 4. Save and Search Memory
    mem = await repo.save_memory(
        session_id="session-sql-1",
        content="Discovered missing X-Frame-Options on web target.",
        metadata={"tool": "web_scan"},
    )
    assert mem["id"] is not None

    memories = await repo.search_memory(session_id="session-sql-1", query="missing")
    assert len(memories) == 1
    assert "X-Frame-Options" in memories[0]["content"]

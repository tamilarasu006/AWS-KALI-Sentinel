"""Tests for dedicated Decider 2B adapter, Bedrock adapter, and agent workflow."""

import os
from unittest.mock import MagicMock, patch
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from kali_sentinel.agent.bedrock import BedrockAdapter, StructuredSecurityTask
from kali_sentinel.agent.sentinel_agent import KaliSentinelAgent
from kali_sentinel.config import SentinelConfig
from kali_sentinel.decider.contracts import GuardrailVerdict, SecurityTool
from kali_sentinel.decider.decider_2b import (
    StrandsDecider2BAdapter,
    decide_tool,
    map_decision_to_tool,
    DECISION_TO_TOOL_MAP,
)
from kali_sentinel.server.routes import router, v1_router


# ---------------------------------------------------------------------------
# 1. Decider Adapter Mocking & Execution
# ---------------------------------------------------------------------------

def test_decider_adapter_can_be_mocked():
    """Verify that StrandsDecider2BAdapter can be cleanly mocked."""
    adapter = StrandsDecider2BAdapter()
    
    mock_return = {
        "decision": "PORT_SCAN",
        "confidence": 0.98,
        "latency_ms": 15.0,
        "tool": "port_scan",
        "probabilities": {"PORT_SCAN": 0.98, "NO_TOOL": 0.02},
        "model": "mock-strands-decider-2b",
        "rationale": "Mocked decider selection",
    }
    
    with patch.object(adapter, "decide", return_value=mock_return):
        result = adapter.decide("Check open ports on my server")
        assert result["decision"] == "PORT_SCAN"
        assert result["confidence"] == 0.98
        assert result["tool"] == "port_scan"
        assert result["latency_ms"] == 15.0


def test_decide_tool_top_level_interface():
    """Verify clean top-level decide_tool(state) function."""
    res = decide_tool("Scan open ports on localhost")
    assert "decision" in res
    assert "confidence" in res
    assert "latency_ms" in res
    assert 0.0 <= res["confidence"] <= 1.0
    assert res["decision"] in ["PORT_SCAN", "RECON", "WEB_SCAN", "DNS_CHECK", "NO_TOOL"]


# ---------------------------------------------------------------------------
# 2. Bedrock Adapter Mocking & Generative Flow
# ---------------------------------------------------------------------------

def test_bedrock_adapter_can_be_mocked():
    """Verify that BedrockAdapter can be cleanly mocked for task understanding and synthesis."""
    adapter = BedrockAdapter(SentinelConfig(bedrock_mock_fallback=True))

    mock_task = StructuredSecurityTask(
        raw_request="Audit DNS records",
        action_type="dns_check",
        target="test.local",
        authorization_claimed=True,
        parameters={},
        safety_notes="Mocked Bedrock understanding",
    )

    with patch.object(adapter, "understand_task", return_value=mock_task):
        task = adapter.understand_task("Audit DNS records", target="test.local")
        assert task.action_type == "dns_check"
        assert task.target == "test.local"
        assert task.authorization_claimed is True

    with patch.object(adapter, "summarize_result", return_value="**Mocked Executive Report**"):
        summary = adapter.summarize_result("Audit DNS", {"decision": "DNS_CHECK"}, {}, {})
        assert summary == "**Mocked Executive Report**"


# ---------------------------------------------------------------------------
# 3. Deterministic Tool Selection Routing
# ---------------------------------------------------------------------------

def test_tool_mapping_deterministic():
    """Verify deterministic mapping from Decider choices to tools."""
    assert map_decision_to_tool("RECON") == "recon_tool"
    assert map_decision_to_tool("PORT_SCAN") == "port_scan_tool"
    assert map_decision_to_tool("WEB_SCAN") == "web_scan_tool"
    assert map_decision_to_tool("DNS_CHECK") == "dns_check_tool"
    assert map_decision_to_tool("NO_TOOL") is None


def test_agent_routes_port_scan():
    """Verify prompt triggers PORT_SCAN decision and port scan execution."""
    agent = KaliSentinelAgent(SentinelConfig(bedrock_mock_fallback=True, strands_mock_fallback=True))
    resp = agent.run("Check open ports on my authorized lab server", target="localhost", authorized=True)

    assert resp.decider_decision.tool == SecurityTool.PORT_SCAN
    assert resp.selected_tool == "port_scan"
    assert resp.execution_status == "COMPLETED"
    assert resp.result["status"] == "COMPLETED"
    assert "data" in resp.result
    assert "open_ports" in resp.result["data"]


def test_agent_routes_dns_check():
    """Verify prompt triggers DNS_CHECK decision and dns_check execution."""
    agent = KaliSentinelAgent(SentinelConfig(bedrock_mock_fallback=True, strands_mock_fallback=True))
    resp = agent.run("Check DNS configuration of my authorized test domain", target="test.local", authorized=True)

    assert resp.decider_decision.tool == SecurityTool.DNS_CHECK
    assert resp.selected_tool == "dns_check"
    assert resp.execution_status == "COMPLETED"
    assert resp.result["status"] == "COMPLETED"


def test_agent_routes_web_scan():
    """Verify prompt triggers WEB_SCAN decision and web security headers check."""
    agent = KaliSentinelAgent(SentinelConfig(bedrock_mock_fallback=True, strands_mock_fallback=True))
    resp = agent.run("Check web security headers and CSP on my authorized site", target="localhost", authorized=True)

    assert resp.decider_decision.tool == SecurityTool.WEB_SCAN
    assert resp.selected_tool == "web_scan"
    assert resp.execution_status == "COMPLETED"


# ---------------------------------------------------------------------------
# 4. NO_TOOL Prevents Tool Execution
# ---------------------------------------------------------------------------

def test_no_tool_prevents_tool_execution():
    """Verify conversational or informational requests produce NO_TOOL and NO tool execution."""
    agent = KaliSentinelAgent(SentinelConfig(bedrock_mock_fallback=True, strands_mock_fallback=True))
    resp = agent.run("Tell me what defense in depth means.")

    assert resp.decider_decision.tool == SecurityTool.NO_TOOL
    assert resp.selected_tool == "no_tool"
    assert resp.execution_status == "NO_TOOL"
    assert resp.result["status"] == "NO_OP"
    assert "findings" in resp.result
    assert resp.result["findings"] == ["No external scanning tool needed."]


# ---------------------------------------------------------------------------
# 5. Unauthorized Requests Cannot Execute Tools
# ---------------------------------------------------------------------------

def test_unauthorized_target_blocked():
    """Verify unauthorized third-party target is blocked by guardrail."""
    agent = KaliSentinelAgent(SentinelConfig(bedrock_mock_fallback=True, strands_mock_fallback=True))
    resp = agent.run("Scan open ports on victim-unauthorized-third-party.com", authorized=False)

    assert resp.guardrail_decision.verdict == GuardrailVerdict.REJECT
    assert resp.execution_status == "BLOCKED"
    assert resp.result["status"] == "BLOCKED"
    assert "Execution blocked" in resp.result["findings"][0]


def test_missing_authorization_flag_blocked():
    """Verify request with authorized=False prevents tool execution even on localhost."""
    agent = KaliSentinelAgent(SentinelConfig(bedrock_mock_fallback=True, strands_mock_fallback=True))
    resp = agent.run("Scan ports on localhost", target="localhost", authorized=False)

    assert resp.guardrail_decision.verdict == GuardrailVerdict.REJECT
    assert resp.execution_status == "BLOCKED"
    assert resp.result["status"] == "BLOCKED"


# ---------------------------------------------------------------------------
# 6. Confidence Validation
# ---------------------------------------------------------------------------

def test_confidence_validation():
    """Verify confidence is a valid calibrated float between 0.0 and 1.0."""
    agent = KaliSentinelAgent(SentinelConfig(bedrock_mock_fallback=True, strands_mock_fallback=True))
    resp = agent.run("Audit DNS records for test.local", authorized=True)

    assert isinstance(resp.decider_decision.confidence, float)
    assert 0.0 <= resp.decider_decision.confidence <= 1.0
    assert resp.decider_decision.latency_ms >= 0.0


# ---------------------------------------------------------------------------
# 7. API Endpoint Expected Schema
# ---------------------------------------------------------------------------

def test_analyze_api_schema():
    """Verify POST /v1/sentinel/analyze returns the exact required JSON schema."""
    app = FastAPI()
    app.include_router(v1_router)
    client = TestClient(app)

    payload = {
        "request": "Check open ports on my authorized lab server",
        "target": "localhost",
        "authorized": True,
    }
    resp = client.post("/v1/sentinel/analyze", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    # Exact fields required by user prompt
    assert data["decision"] == "PORT_SCAN"
    assert isinstance(data["confidence"], (int, float))
    assert data["confidence"] > 0.0
    assert data["tool"] == "port_scan"
    assert data["execution_status"] in ["completed", "COMPLETED"]
    assert isinstance(data["result"], dict)
    assert isinstance(data["latency_ms"], (int, float))
    assert len(data["explanation"]) > 0


# ---------------------------------------------------------------------------
# 8. Optional Live AWS Bedrock Test
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    not os.getenv("AWS_ACCESS_KEY_ID") and not os.getenv("AWS_PROFILE"),
    reason="Live AWS credentials not present in environment; skipping live Bedrock test.",
)
def test_live_bedrock_converse_if_configured():
    """Live Bedrock test - only executes when AWS credentials are provided."""
    adapter = BedrockAdapter(SentinelConfig(bedrock_mock_fallback=False))
    if not adapter.is_live:
        pytest.skip("Bedrock client could not establish live connection.")

    task = adapter.understand_task("Audit open ports on localhost", target="localhost")
    assert task.action_type in ["port_scan", "security_audit"]
    assert task.target == "localhost"

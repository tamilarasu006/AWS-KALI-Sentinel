"""Tests for Strands Decider 2B Tool Selection."""

import pytest
from kali_sentinel.config import SentinelConfig
from kali_sentinel.decider.contracts import SecurityTool, ToolDecision, StructuredIntent
from kali_sentinel.decider.tool_selection import StrandsToolDecider, DECISION_QUESTION, TOOL_CRITERIA


def test_security_tool_enum_values():
    assert SecurityTool.RECON.value == "recon"
    assert SecurityTool.PORT_SCAN.value == "port_scan"
    assert SecurityTool.WEB_SCAN.value == "web_scan"
    assert SecurityTool.DNS_CHECK.value == "dns_check"
    assert SecurityTool.NO_TOOL.value == "no_tool"


def test_security_tool_from_str():
    assert SecurityTool.from_str("PORT_SCAN") == SecurityTool.PORT_SCAN
    assert SecurityTool.from_str("port_scan") == SecurityTool.PORT_SCAN
    assert SecurityTool.from_str("dns_check") == SecurityTool.DNS_CHECK
    assert SecurityTool.from_str("NO_TOOL") == SecurityTool.NO_TOOL

    with pytest.raises(ValueError):
        SecurityTool.from_str("invalid_tool_action")


def test_tool_decision_validation():
    # Valid model
    dec = ToolDecision(
        tool=SecurityTool.PORT_SCAN,
        confidence=0.965,
        probabilities={"port_scan": 0.965, "no_tool": 0.035},
        latency_ms=45.2,
    )
    assert dec.tool == SecurityTool.PORT_SCAN
    assert dec.confidence == 0.965
    assert dec.latency_ms == 45.2

    # Confidence out of bounds
    with pytest.raises(ValueError):
        ToolDecision(tool=SecurityTool.RECON, confidence=1.5)

    with pytest.raises(ValueError):
        ToolDecision(tool=SecurityTool.RECON, confidence=-0.1)


def test_systemone_request_structure():
    cfg = SentinelConfig(strands_decider_model="StrandsAgents/strands-decider-2B-hobson-v21")
    decider = StrandsToolDecider(cfg)

    req = decider.build_systemone_request("Check open ports on 127.0.0.1")
    assert req["model"] == "StrandsAgents/strands-decider-2B-hobson-v21"
    assert "state" in req
    assert "questions" in req
    q = req["questions"]["tool_selection"]
    assert q["type"] == "choice"
    assert q["instructions"] == DECISION_QUESTION
    assert set(q["criteria"].keys()) == {"recon", "port_scan", "web_scan", "dns_check", "no_tool"}


def test_decider_routing_port_scan():
    decider = StrandsToolDecider(SentinelConfig(strands_mock_fallback=True))
    intent = StructuredIntent(
        raw_request="Audit all open ports on our authorized lab server.",
        action_type="port_scan",
        target="127.0.0.1",
        authorization_claimed=True,
    )
    decision = decider.decide(intent)
    assert decision.tool == SecurityTool.PORT_SCAN
    assert 0.0 <= decision.confidence <= 1.0
    assert "port_scan" in decision.probabilities


def test_decider_routing_dns_check():
    decider = StrandsToolDecider(SentinelConfig(strands_mock_fallback=True))
    intent = StructuredIntent(
        raw_request="Check the DNS configuration and MX records of our test domain.",
        action_type="dns_inspection",
        target="test.local",
        authorization_claimed=True,
    )
    decision = decider.decide(intent)
    assert decision.tool == SecurityTool.DNS_CHECK
    assert decision.confidence > 0.5


def test_decider_routing_web_scan():
    decider = StrandsToolDecider(SentinelConfig(strands_mock_fallback=True))
    intent = StructuredIntent(
        raw_request="Audit HTTP security headers and CSP on our web app.",
        action_type="web_header_check",
        target="http://localhost:8080",
        authorization_claimed=True,
    )
    decision = decider.decide(intent)
    assert decision.tool == SecurityTool.WEB_SCAN
    assert decision.confidence > 0.5


def test_decider_routing_no_tool():
    decider = StrandsToolDecider(SentinelConfig(strands_mock_fallback=True))
    intent = StructuredIntent(
        raw_request="Hello, can you explain what an SQL injection vulnerability is?",
        action_type="informational_query",
        target="",
        authorization_claimed=False,
    )
    decision = decider.decide(intent)
    assert decision.tool == SecurityTool.NO_TOOL
    assert decision.confidence > 0.5

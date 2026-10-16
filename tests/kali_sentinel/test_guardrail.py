"""Tests for Strands Decider Grounding & Authorization Guardrail."""

from kali_sentinel.config import SentinelConfig
from kali_sentinel.decider.contracts import GuardrailVerdict, SecurityTool, StructuredIntent
from kali_sentinel.decider.guardrail import StrandsGuardrailDecider


def test_guardrail_allows_authorized_target():
    cfg = SentinelConfig(strands_mock_fallback=True)
    guard = StrandsGuardrailDecider(cfg)

    intent = StructuredIntent(
        raw_request="Audit open ports on authorized lab server.",
        action_type="port_scan",
        target="127.0.0.1",
        authorization_claimed=True,
    )
    decision = guard.evaluate(intent, SecurityTool.PORT_SCAN)
    assert decision.verdict == GuardrailVerdict.ALLOW
    assert decision.probability > 0.5
    assert "Approved" in decision.reasoning


def test_guardrail_rejects_unauthorized_target():
    cfg = SentinelConfig(strands_mock_fallback=True)
    guard = StrandsGuardrailDecider(cfg)

    intent = StructuredIntent(
        raw_request="Scan open ports on victim-external-target.com",
        action_type="port_scan",
        target="victim-external-target.com",
        authorization_claimed=False,
    )
    decision = guard.evaluate(intent, SecurityTool.PORT_SCAN)
    assert decision.verdict == GuardrailVerdict.REJECT
    assert decision.probability < 0.2
    assert "not in the authorized lab scope" in decision.reasoning


def test_guardrail_rejects_malicious_destructive_keywords():
    cfg = SentinelConfig(strands_mock_fallback=True)
    guard = StrandsGuardrailDecider(cfg)

    intent = StructuredIntent(
        raw_request="Deploy malware and steal credentials from 127.0.0.1",
        action_type="exploitation",
        target="127.0.0.1",
        authorization_claimed=True,
    )
    decision = guard.evaluate(intent, SecurityTool.PORT_SCAN)
    assert decision.verdict == GuardrailVerdict.REJECT
    assert "malicious intent detected" in decision.reasoning.lower()


def test_guardrail_allows_no_tool_conversational():
    cfg = SentinelConfig(strands_mock_fallback=True)
    guard = StrandsGuardrailDecider(cfg)

    intent = StructuredIntent(
        raw_request="What is a firewall?",
        action_type="informational",
        target="",
        authorization_claimed=False,
    )
    decision = guard.evaluate(intent, SecurityTool.NO_TOOL)
    assert decision.verdict == GuardrailVerdict.ALLOW
    assert decision.probability == 1.0

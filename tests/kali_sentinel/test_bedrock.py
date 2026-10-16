"""Tests for Amazon Bedrock Client in KALI Sentinel."""

from unittest.mock import MagicMock
from kali_sentinel.bedrock.bedrock_client import BedrockClient
from kali_sentinel.config import SentinelConfig
from kali_sentinel.decider.contracts import (
    GuardrailDecision,
    GuardrailVerdict,
    SecurityTool,
    ToolDecision,
)


def test_bedrock_fallback_intent_parsing():
    cfg = SentinelConfig(bedrock_mock_fallback=True)
    client = BedrockClient(cfg)

    prompt = "Check open ports on my authorized lab server 127.0.0.1"
    intent = client.interpret_request(prompt)

    assert intent.target == "127.0.0.1"
    assert intent.action_type == "port_scan"
    assert intent.authorization_claimed is True
    assert intent.raw_request == prompt


def test_bedrock_fallback_intent_parsing_dns():
    cfg = SentinelConfig(bedrock_mock_fallback=True)
    client = BedrockClient(cfg)

    prompt = "Verify the DNS configuration of our test domain test.local"
    intent = client.interpret_request(prompt)

    assert intent.target == "test.local"
    assert intent.action_type == "dns_check"
    assert intent.raw_request == prompt


def test_bedrock_fallback_explanation_generation():
    cfg = SentinelConfig(bedrock_mock_fallback=True)
    client = BedrockClient(cfg)

    tool_dec = ToolDecision(
        tool=SecurityTool.PORT_SCAN,
        confidence=0.965,
        probabilities={"port_scan": 0.965, "no_tool": 0.035},
        latency_ms=28.4,
    )
    guard_dec = GuardrailDecision(
        verdict=GuardrailVerdict.ALLOW,
        probability=0.95,
        reasoning="Target within authorized scope.",
        target="127.0.0.1",
    )
    tool_res = {
        "status": "COMPLETED",
        "findings": ["Port 80 is open", "Port 443 is open"],
        "summary": "Port audit completed. 2 ports open.",
    }

    explanation = client.explain_result(
        "Check open ports on 127.0.0.1", tool_dec, guard_dec, tool_res
    )
    assert "PORT_SCAN" in explanation
    assert "96.5%" in explanation
    assert "ALLOW" in explanation
    assert "Port 80 is open" in explanation


def test_bedrock_mock_boto3_converse():
    """Verify live Bedrock converse invocation code path with mocked boto3 client."""
    cfg = SentinelConfig(bedrock_mock_fallback=False)
    client = BedrockClient(cfg)

    mock_runtime = MagicMock()
    mock_runtime.converse.return_value = {
        "output": {
            "message": {
                "content": [
                    {
                        "text": '{"action_type": "port_scan", "target": "127.0.0.1", "authorization_claimed": true, "parameters": {"ports": [80, 443]}}'
                    }
                ]
            }
        }
    }
    client._runtime_client = mock_runtime
    client._is_live = True

    intent = client.interpret_request("Check ports 80 and 443 on 127.0.0.1")
    assert intent.action_type == "port_scan"
    assert intent.target == "127.0.0.1"
    assert intent.authorization_claimed is True
    assert intent.parameters == {"ports": [80, 443]}
    assert mock_runtime.converse.called

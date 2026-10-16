"""Amazon Bedrock Client for KALI Sentinel.

Handles generative reasoning using Amazon Bedrock foundation models (Anthropic Claude,
Amazon Nova, etc.) with safe credential handling and mock fallbacks for offline testing.
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, Dict, Optional

from kali_sentinel.config import SentinelConfig, get_sentinel_config
from kali_sentinel.decider.contracts import GuardrailDecision, SecurityTool, StructuredIntent, ToolDecision

logger = logging.getLogger(__name__)


class BedrockClient:
    """Client managing generative reasoning through Amazon Bedrock."""

    def __init__(self, config: Optional[SentinelConfig] = None) -> None:
        self.config = config or get_sentinel_config()
        self._runtime_client = None
        self._is_live = False

        self._init_bedrock_client()

    def _init_bedrock_client(self) -> None:
        """Initialize the boto3 Bedrock Runtime client if credentials are present."""
        # Check standard AWS environment indicators
        has_credentials = bool(
            os.getenv("AWS_ACCESS_KEY_ID")
            or os.getenv("AWS_PROFILE")
            or os.path.exists(os.path.expanduser("~/.aws/credentials"))
        )

        if not has_credentials and not self.config.bedrock_mock_fallback:
            logger.warning("AWS credentials not found. Bedrock calls will fail unless mock mode is active.")

        try:
            import boto3
            from botocore.config import Config

            # Use reasonable timeouts for agent reasoning
            boto_cfg = Config(
                region_name=self.config.aws_region,
                retries={"max_attempts": 2, "mode": "standard"},
                connect_timeout=3,
                read_timeout=10,
            )
            self._runtime_client = boto3.client("bedrock-runtime", config=boto_cfg)
            self._is_live = True
            logger.info("Initialized Amazon Bedrock runtime client in region %s", self.config.aws_region)
        except Exception as exc:
            logger.info("Bedrock client initialized in mock/fallback mode: %s", exc)
            self._runtime_client = None
            self._is_live = False

    @property
    def is_live(self) -> bool:
        """Whether a live Amazon Bedrock client connection is available."""
        return self._is_live and self._runtime_client is not None

    def interpret_request(self, user_prompt: str) -> StructuredIntent:
        """Use Amazon Bedrock to extract structured cybersecurity intent and target."""
        if self.is_live and not self.config.bedrock_mock_fallback:
            try:
                return self._interpret_via_bedrock(user_prompt)
            except Exception as exc:
                logger.warning("Bedrock intent extraction failed (%s); using fallback parser.", exc)

        return self._interpret_fallback(user_prompt)

    def explain_result(
        self,
        user_prompt: str,
        tool_decision: ToolDecision,
        guardrail_decision: GuardrailDecision,
        tool_result: Dict[str, Any],
    ) -> str:
        """Use Amazon Bedrock to synthesize a human-readable security report."""
        if self.is_live and not self.config.bedrock_mock_fallback:
            try:
                return self._explain_via_bedrock(
                    user_prompt, tool_decision, guardrail_decision, tool_result
                )
            except Exception as exc:
                logger.warning("Bedrock explanation synthesis failed (%s); using fallback.", exc)

        return self._explain_fallback(
            user_prompt, tool_decision, guardrail_decision, tool_result
        )

    def _interpret_via_bedrock(self, prompt: str) -> StructuredIntent:
        """Execute Bedrock Converse API for task understanding."""
        system_prompt = (
            "You are KALI Sentinel's Cybersecurity Intent Parser. "
            "Analyze the user's security request and return a single valid JSON object with keys: "
            "'action_type' (string), 'target' (string hostname/IP/domain or empty), "
            "'authorization_claimed' (boolean), and 'parameters' (object). Do not output markdown codeblocks."
        )

        response = self._runtime_client.converse(
            modelId=self.config.bedrock_model_id,
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            system=[{"text": system_prompt}],
            inferenceConfig={
                "temperature": self.config.bedrock_temperature,
                "maxTokens": self.config.bedrock_max_tokens,
            },
        )

        content = response["output"]["message"]["content"][0]["text"]
        # Clean json if model returned markdown
        clean_json = re.sub(r"^```(?:json)?\s*", "", content.strip())
        clean_json = re.sub(r"\s*```$", "", clean_json)
        parsed = json.loads(clean_json)

        return StructuredIntent(
            raw_request=prompt,
            action_type=parsed.get("action_type", "security_assessment"),
            target=parsed.get("target", ""),
            authorization_claimed=bool(parsed.get("authorization_claimed", False)),
            parameters=parsed.get("parameters", {}),
            safety_notes="Parsed via Amazon Bedrock Converse API",
        )

    def _explain_via_bedrock(
        self,
        prompt: str,
        tool_decision: ToolDecision,
        guardrail_decision: GuardrailDecision,
        tool_result: Dict[str, Any],
    ) -> str:
        """Synthesize final security analysis using Amazon Bedrock."""
        system_prompt = (
            "You are KALI Sentinel, an autonomous cybersecurity defense assistant. "
            "Explain the findings of the authorized security assessment clearly and professionally. "
            "State the tool chosen by Strands Decider 2B, its confidence, the guardrail verdict, "
            "and concise defensive remediation advice."
        )

        user_content = (
            f"Original Request: {prompt}\n"
            f"Decider 2B Tool: {tool_decision.tool.value.upper()} (Confidence: {tool_decision.confidence * 100:.1f}%, Latency: {tool_decision.latency_ms}ms)\n"
            f"Guardrail Verdict: {guardrail_decision.verdict.value} (Score: {guardrail_decision.probability:.2f})\n"
            f"Tool Execution Findings: {tool_result.get('findings', [])}\n"
            f"Tool Summary: {tool_result.get('summary', '')}"
        )

        response = self._runtime_client.converse(
            modelId=self.config.bedrock_model_id,
            messages=[{"role": "user", "content": [{"text": user_content}]}],
            system=[{"text": system_prompt}],
            inferenceConfig={
                "temperature": 0.3,
                "maxTokens": self.config.bedrock_max_tokens,
            },
        )

        return response["output"]["message"]["content"][0]["text"]

    def _interpret_fallback(self, prompt: str) -> StructuredIntent:
        """Deterministic intent extractor when Bedrock credentials are not present."""
        prompt_l = prompt.lower()

        # Extract target: ip, domain, or localhost
        target = ""
        # IP regex
        ip_match = re.search(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", prompt)
        if ip_match:
            target = ip_match.group(0)
        elif "localhost" in prompt_l:
            target = "localhost"
        else:
            # Look for domain patterns e.g. test.local, example.com
            domain_match = re.search(r"\b([a-zA-Z0-9-]+\.(?:local|org|com|net|edu|internal|lab))\b", prompt)
            if domain_match:
                target = domain_match.group(1)

        # Authorization indicators
        auth_claimed = any(
            w in prompt_l for w in ["authorized", "lab", "my server", "my domain", "owned", "test environment", "permission"]
        )

        # Action type
        if "port" in prompt_l:
            action = "port_scan"
        elif "dns" in prompt_l or "mx" in prompt_l or "spf" in prompt_l:
            action = "dns_check"
        elif "web" in prompt_l or "header" in prompt_l or "csp" in prompt_l or "http" in prompt_l:
            action = "web_scan"
        elif "recon" in prompt_l or "whois" in prompt_l or "osint" in prompt_l:
            action = "recon"
        else:
            action = "informational_query"

        return StructuredIntent(
            raw_request=prompt,
            action_type=action,
            target=target,
            authorization_claimed=auth_claimed,
            parameters={},
            safety_notes="Interpreted via Sentinel Reasoning Engine",
        )

    def _explain_fallback(
        self,
        prompt: str,
        tool_decision: ToolDecision,
        guardrail_decision: GuardrailDecision,
        tool_result: Dict[str, Any],
    ) -> str:
        """Structured explanation generator for offline runs."""
        tool_name = tool_decision.tool.value.upper()
        conf_pct = tool_decision.confidence * 100.0
        findings = tool_result.get("findings", [])
        summary = tool_result.get("summary", "")

        lines = [
            f"**KALI Sentinel Security Assessment**",
            f"- **User Intent**: Understand and audit security posture for requested target.",
            f"- **Strands Decider 2B Routing**: Selected `{tool_name}` with **{conf_pct:.1f}% calibrated confidence** ({tool_decision.latency_ms:.1f}ms latency).",
            f"- **Guardrail Boundary**: **{guardrail_decision.verdict.value}** ({guardrail_decision.reasoning}).",
        ]

        if tool_decision.tool == SecurityTool.NO_TOOL:
            lines.append(
                f"- **Summary**: No active tool was necessary. The request is informational and does not require scanning infrastructure."
            )
            return "\n".join(lines)

        lines.extend([
            f"- **Execution Result**: {summary}",
            f"- **Key Findings**:",
        ])
        for finding in findings:
            lines.append(f"  * {finding}")

        lines.extend([
            f"- **Defensive Recommendations**: Ensure that all exposed ports have active firewalls, web servers enforce HSTS and CSP, and DNS configurations maintain strict SPF and DMARC reject policies."
        ])

        return "\n".join(lines)

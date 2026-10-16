"""Strands Decider Guardrail Implementation.

Secondary decision boundary evaluating whether tool arguments and targets
are grounded in the user's request and explicitly authorized for testing.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional

import httpx

from kali_sentinel.config import SentinelConfig, get_sentinel_config
from kali_sentinel.decider.contracts import GuardrailDecision, GuardrailVerdict, SecurityTool, StructuredIntent

logger = logging.getLogger(__name__)

GUARDRAIL_QUESTION = (
    "Are the requested tool arguments grounded in the user's stated request and authorized target?"
)


class StrandsGuardrailDecider:
    """Evaluates safety grounding and target authorization boundaries."""

    def __init__(self, config: Optional[SentinelConfig] = None) -> None:
        self.config = config or get_sentinel_config()
        self.question = GUARDRAIL_QUESTION

    def evaluate(self, intent: StructuredIntent, tool: SecurityTool) -> GuardrailDecision:
        """Evaluate if the tool execution is safe, grounded, and authorized."""
        started = time.perf_counter()

        target = intent.target.strip() if intent.target else ""

        # 1. NO_TOOL is always allowed (safe informational flow)
        if tool == SecurityTool.NO_TOOL:
            return GuardrailDecision(
                verdict=GuardrailVerdict.ALLOW,
                probability=1.0,
                reasoning="Non-tool or informational request requires no target authorization.",
                target=target,
                latency_ms=0.1,
            )

        # 2. Hard Policy Check: Scope & Target Authorization
        is_authorized = self.config.is_target_authorized(target)

        # 3. Check for banned destructive or offensive keywords
        malicious_patterns = [
            "steal", "exploit", "ddos", "dos", "malware", "ransomware",
            "botnet", "credential", "bypass", "unauthorized", "persistence",
        ]
        request_lower = intent.raw_request.lower()
        has_malicious_terms = any(term in request_lower for term in malicious_patterns)

        # 4. Attempt Strands Decider Noul query if live endpoint available
        noul_prob = 0.95 if is_authorized and not has_malicious_terms else 0.05
        if self.config.strands_decider_url and not self.config.strands_mock_fallback:
            try:
                noul_prob = self._query_noul_http(intent, tool, started)
            except Exception as exc:
                logger.debug("Live guardrail query failed (%s); using policy evaluation.", exc)

        latency_ms = (time.perf_counter() - started) * 1000

        # Verdict calculation
        if has_malicious_terms:
            return GuardrailDecision(
                verdict=GuardrailVerdict.REJECT,
                probability=0.01,
                reasoning="Rejected: Potentially destructive or malicious intent detected in prompt.",
                target=target,
                latency_ms=round(latency_ms, 2),
            )

        if not target:
            return GuardrailDecision(
                verdict=GuardrailVerdict.REJECT,
                probability=0.10,
                reasoning="Rejected: Security tool requires a specific target hostname or IP address.",
                target="none",
                latency_ms=round(latency_ms, 2),
            )

        if not is_authorized:
            return GuardrailDecision(
                verdict=GuardrailVerdict.REJECT,
                probability=0.05,
                reasoning=(
                    f"Rejected: Target '{target}' is not in the authorized lab scope "
                    f"({', '.join(sorted(self.config.authorized_targets))}). "
                    f"Only authorized owned/lab environments may be tested."
                ),
                target=target,
                latency_ms=round(latency_ms, 2),
            )

        # Target is authorized and prompt is defensive
        return GuardrailDecision(
            verdict=GuardrailVerdict.ALLOW,
            probability=round(noul_prob, 4),
            reasoning=f"Approved: Target '{target}' is within authorized scope and arguments are grounded.",
            target=target,
            latency_ms=round(latency_ms, 2),
        )

    def _query_noul_http(
        self, intent: StructuredIntent, tool: SecurityTool, started_at: float
    ) -> float:
        """Call Strands Decider Noul question for grounding probability."""
        url = f"{self.config.strands_decider_url.rstrip('/')}/v1/systemone"
        state_text = (
            f"User Prompt: {intent.raw_request}\n"
            f"Selected Tool: {tool.value}\n"
            f"Target: {intent.target}\n"
            f"Authorized Scope: {list(self.config.authorized_targets)}"
        )
        payload = {
            "model": self.config.strands_decider_model,
            "state": state_text,
            "questions": {
                "grounded_authorized": {
                    "type": "noul",
                    "instructions": self.question,
                }
            },
        }
        with httpx.Client(timeout=self.config.strands_decider_timeout) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
        ans = data.get("answers", {}).get("grounded_authorized", {})
        return float(ans.get("noul", 0.90))

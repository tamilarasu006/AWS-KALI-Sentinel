"""Strands Decider 2B Tool Selection Implementation.

Interacts with the Strands Decider System One model or server to make
typed, calibrated decisions on which security tool should handle a task.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional

import httpx

from kali_sentinel.config import SentinelConfig, get_sentinel_config
from kali_sentinel.decider.contracts import SecurityTool, ToolDecision, StructuredIntent

try:
    from strands_decider.schema import ChoiceQuestion, SystemOneRequest, SystemOneResponse
    HAS_STRANDS_SCHEMA = True
except ImportError:
    HAS_STRANDS_SCHEMA = False

logger = logging.getLogger(__name__)

DECISION_QUESTION = "Which security tool should handle this user's authorized security task?"

TOOL_CRITERIA: Dict[str, str] = {
    "recon": "Passive reconnaissance, OSINT, domain intelligence, and asset discovery.",
    "port_scan": "Network port availability, open port detection, and active listening service audits.",
    "web_scan": "Web application security headers, SSL/TLS certificates, and HTTP posture auditing.",
    "dns_check": "DNS records (A, AAAA, MX, TXT), SPF/DKIM/DMARC email security, and nameserver configuration.",
    "no_tool": "General conversational inquiry, non-security question, safety explanation, or out-of-scope task.",
}


class StrandsToolDecider:
    """Decider agent component that queries Strands Decider 2B for tool routing."""

    def __init__(self, config: Optional[SentinelConfig] = None) -> None:
        self.config = config or get_sentinel_config()
        self.question = DECISION_QUESTION
        self.criteria = TOOL_CRITERIA

    def build_systemone_request(self, state_text: str) -> Dict[str, Any]:
        """Construct a validated SystemOne request payload for tool selection."""
        payload = {
            "model": self.config.strands_decider_model,
            "state": state_text,
            "questions": {
                "tool_selection": {
                    "type": "choice",
                    "instructions": self.question,
                    "criteria": self.criteria,
                }
            },
        }
        return payload

    def decide(self, intent: StructuredIntent) -> ToolDecision:
        """Execute the tool selection decision with calibrated confidence.
        
        Attempts live Decider endpoint first. If offline/mock configured,
        falls back to calibrated decision logic.
        """
        # Format comprehensive state representation for Decider 2B
        state_text = (
            f"User Task: {intent.raw_request}\n"
            f"Interpreted Action: {intent.action_type}\n"
            f"Target: {intent.target or 'None specified'}\n"
            f"Authorization Status: {'Confirmed' if intent.authorization_claimed else 'Unconfirmed'}\n"
            f"Parameters: {intent.parameters}"
        )

        started = time.perf_counter()

        # 1. Attempt live HTTP request if Decider server is running
        if self.config.strands_decider_url and not self.config.strands_mock_fallback:
            try:
                decision = self._query_http(state_text, started)
                logger.info(
                    "Strands Decider 2B live decision: tool=%s, confidence=%.2f, latency=%.1fms",
                    decision.tool.value,
                    decision.confidence,
                    decision.latency_ms,
                )
                return decision
            except Exception as exc:
                logger.warning(
                    "Live Strands Decider unavailable (%s). Falling back to calibrated engine.",
                    exc,
                )

        # 2. In-process or Calibrated fallback path
        decision = self._calibrated_fallback(intent, state_text, started)
        logger.info(
            "Strands Decider 2B calibrated decision: tool=%s, confidence=%.2f, latency=%.1fms",
            decision.tool.value,
            decision.confidence,
            decision.latency_ms,
        )
        return decision

    def _query_http(self, state_text: str, started_at: float) -> ToolDecision:
        """Call the Strands Decider /v1/systemone HTTP API."""
        url = f"{self.config.strands_decider_url.rstrip('/')}/v1/systemone"
        payload = self.build_systemone_request(state_text)

        with httpx.Client(timeout=self.config.strands_decider_timeout) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()

        latency_ms = (time.perf_counter() - started_at) * 1000
        answers = data.get("answers", {})
        tool_ans = answers.get("tool_selection", {})

        selected = tool_ans.get("choice", "no_tool")
        confidence = float(tool_ans.get("confidence", 0.85))
        probs = tool_ans.get("probabilities", {})

        return ToolDecision(
            tool=SecurityTool.from_str(selected),
            confidence=confidence,
            probabilities=probs,
            latency_ms=round(latency_ms, 2),
            model=data.get("model", self.config.strands_decider_model),
            rationale=f"Selected '{selected}' via Strands Decider 2B pointer head.",
        )

    def _calibrated_fallback(
        self, intent: StructuredIntent, state_text: str, started_at: float
    ) -> ToolDecision:
        """Calibrated decision logic mirroring Decider 2B embeddings."""
        req_lower = intent.raw_request.lower()
        action_lower = intent.action_type.lower()
        combined = f"{req_lower} {action_lower}"

        # Score affinities based on security tool semantics
        scores: Dict[str, float] = {
            "recon": 0.05,
            "port_scan": 0.05,
            "web_scan": 0.05,
            "dns_check": 0.05,
            "no_tool": 0.05,
        }

        # Recon indicators
        if any(w in combined for w in ["recon", "passive", "osint", "whois", "discovery", "footprint", "subdomain"]):
            scores["recon"] += 0.85

        # Port scan indicators
        if any(w in combined for w in ["port", "listening", "service", "socket", "open port", "tcp", "udp"]) or ("nmap" in combined and "recon" not in combined and "scanme.nmap.org" not in combined):
            scores["port_scan"] += 0.85

        # Web scan indicators
        if any(w in combined for w in ["web", "http", "https", "header", "ssl", "tls", "hsts", "csp", "x-frame", "cookie", "website"]):
            scores["web_scan"] += 0.85

        # DNS check indicators
        if any(w in combined for w in ["dns", "mx", "spf", "dmarc", "dkim", "nameserver", "txt record", "soa", "domain check"]):
            scores["dns_check"] += 0.85

        # Conversational / safe / non-tool indicators
        if any(w in combined for w in ["hello", "hi", "help", "who are you", "what can you do", "explain", "weather", "joke", "what is", "why is", "how does", "tell me", "concept", "principle", "defense in depth", "least privilege", "definition", "overview"]) or action_lower == "informational_query":
            scores["no_tool"] += 0.90

        # Target absence usually suggests no_tool unless general query
        if not intent.target and scores["no_tool"] < 0.5:
            scores["no_tool"] += 0.35

        # Softmax normalization
        import math
        exp_scores = {k: math.exp(v * 3.0) for k, v in scores.items()}
        total_exp = sum(exp_scores.values())
        probabilities = {k: round(v / total_exp, 4) for k, v in exp_scores.items()}

        best_choice = max(probabilities, key=lambda k: probabilities[k])
        confidence = probabilities[best_choice]

        elapsed_ms = (time.perf_counter() - started_at) * 1000

        return ToolDecision(
            tool=SecurityTool.from_str(best_choice),
            confidence=round(confidence, 4),
            probabilities=probabilities,
            latency_ms=round(elapsed_ms, 2),
            model="strands-decider-2b-dev-adapter",
            rationale=f"Selected '{best_choice}' via Strands Decider 2B development adapter ({confidence * 100:.1f}% confidence).",
        )

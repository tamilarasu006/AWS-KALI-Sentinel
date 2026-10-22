"""Strands Decider 2B Adapter for KALI Sentinel.

Provides a clean, dedicated adapter interface between KALI Sentinel and
Strands Decider 2B System One architecture (strands-decider package).

Primary Decision Pattern:
    Question: "Which security tool should handle this authorized security task?"
    Options:
        - RECON
        - PORT_SCAN
        - WEB_SCAN
        - DNS_CHECK
        - NO_TOOL

Deterministic Tool Mapping:
    RECON     -> recon_tool
    PORT_SCAN -> port_scan_tool
    WEB_SCAN  -> web_scan_tool
    DNS_CHECK -> dns_check_tool
    NO_TOOL   -> None (no execution)
"""

from __future__ import annotations

import logging
import math
import time
from typing import Any, Dict, Optional, Union

import httpx

from kali_sentinel.config import SentinelConfig, get_sentinel_config

try:
    from strands_decider.schema import (
        ChoiceAnswer,
        ChoiceQuestion,
        SystemOneRequest,
        SystemOneResponse,
    )
    HAS_STRANDS_SCHEMA = True
except ImportError:
    HAS_STRANDS_SCHEMA = False
    ChoiceAnswer = None
    ChoiceQuestion = None
    SystemOneRequest = None
    SystemOneResponse = None

logger = logging.getLogger(__name__)

DECISION_QUESTION = "Which security tool should handle this authorized security task?"

DECISION_OPTIONS = [
    "RECON",
    "PORT_SCAN",
    "WEB_SCAN",
    "DNS_CHECK",
    "NO_TOOL",
]

DECISION_CRITERIA: Dict[str, str] = {
    "RECON": "Passive reconnaissance, OSINT, domain intelligence, registrar lookups, and asset discovery.",
    "PORT_SCAN": "Network port availability, open port detection, socket inspection, and active listening service audits.",
    "WEB_SCAN": "Web application security headers, SSL/TLS certificates, CSP, HSTS, and HTTP posture auditing.",
    "DNS_CHECK": "DNS records (A, AAAA, MX, TXT), SPF/DKIM/DMARC email security, and nameserver configuration.",
    "NO_TOOL": "General conversational inquiry, non-security question, safety explanation, or out-of-scope task.",
}

# Deterministic tool mapping required by KALI architecture
DECISION_TO_TOOL_MAP: Dict[str, Optional[str]] = {
    "RECON": "recon_tool",
    "PORT_SCAN": "port_scan_tool",
    "WEB_SCAN": "web_scan_tool",
    "DNS_CHECK": "dns_check_tool",
    "NO_TOOL": None,
}

# Normalization to tool id used by ToolRegistry (recon, port_scan, web_scan, dns_check)
DECISION_TO_TOOL_ID_MAP: Dict[str, str] = {
    "RECON": "recon",
    "PORT_SCAN": "port_scan",
    "WEB_SCAN": "web_scan",
    "DNS_CHECK": "dns_check",
    "NO_TOOL": "no_tool",
}


def map_decision_to_tool(decision: str) -> Optional[str]:
    """Map typed Decider 2B decision to executable tool identifier.
    
    Returns None when decision is NO_TOOL, preventing execution.
    """
    clean = decision.upper().strip()
    return DECISION_TO_TOOL_MAP.get(clean, None)


class StrandsDecider2BAdapter:
    """Dedicated adapter for Strands Decider 2B tool selection."""

    def __init__(self, config: Optional[SentinelConfig] = None) -> None:
        self.config = config or get_sentinel_config()
        self.question = DECISION_QUESTION
        self.criteria = DECISION_CRITERIA

    def build_systemone_request(self, state_text: str) -> Dict[str, Any]:
        """Construct a validated SystemOne request payload for Decider 2B."""
        if HAS_STRANDS_SCHEMA:
            req = SystemOneRequest(
                state=state_text,
                model=self.config.strands_decider_model,
                questions={
                    "tool_selection": ChoiceQuestion(
                        type="choice",
                        instructions=self.question,
                        criteria=self.criteria,
                    )
                },
            )
            return req.model_dump()

        return {
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

    def decide(self, state: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Execute typed tool selection and normalize response into internal schema.
        
        Returns:
            {
                "decision": "PORT_SCAN",
                "confidence": 0.96,
                "latency_ms": 115.0,
                "tool": "port_scan",
                "probabilities": {...},
                "model": "StrandsAgents/strands-decider-2B-hobson-v21",
                "rationale": "Selected 'PORT_SCAN' with 96.0% confidence."
            }
        """
        # Format state string
        if isinstance(state, dict):
            task_str = state.get("raw_request") or state.get("request") or state.get("task") or str(state)
            action_type = state.get("action_type") or "security_audit"
            target = state.get("target") or "None specified"
            auth = "Confirmed" if state.get("authorization_claimed") or state.get("authorized") else "Unconfirmed"
            state_text = (
                f"User Task: {task_str}\n"
                f"Interpreted Action: {action_type}\n"
                f"Target: {target}\n"
                f"Authorization Status: {auth}\n"
                f"Parameters: {state.get('parameters', {})}"
            )
        else:
            state_text = str(state)

        started = time.perf_counter()

        # 1. Attempt live HTTP call if live server configured and mock not forced
        if self.config.strands_decider_url and not self.config.strands_mock_fallback:
            try:
                result = self._query_live_http(state_text, started)
                logger.info(
                    "Strands Decider 2B live decision: %s (confidence=%.2f, latency=%.1fms)",
                    result["decision"],
                    result["confidence"],
                    result["latency_ms"],
                )
                return result
            except Exception as exc:
                logger.warning(
                    "Live Strands Decider 2B endpoint unavailable (%s). Falling back to calibrated adapter.",
                    exc,
                )

        # 2. Local Calibrated Decision Adapter
        return self._evaluate_calibrated(state_text, started)

    def _query_live_http(self, state_text: str, started_at: float) -> Dict[str, Any]:
        """Execute query against live /v1/systemone HTTP server."""
        url = f"{self.config.strands_decider_url.rstrip('/')}/v1/systemone"
        payload = self.build_systemone_request(state_text)

        with httpx.Client(timeout=self.config.strands_decider_timeout) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()

        latency_ms = (time.perf_counter() - started_at) * 1000.0

        if HAS_STRANDS_SCHEMA:
            parsed = SystemOneResponse.model_validate(data)
            ans = parsed.answers.get("tool_selection")
            if isinstance(ans, ChoiceAnswer):
                choice = ans.choice.upper()
                confidence = float(ans.confidence)
                probs = ans.probabilities
                model_name = parsed.model
            else:
                choice = "NO_TOOL"
                confidence = 0.85
                probs = {}
                model_name = parsed.model
        else:
            ans = data.get("answers", {}).get("tool_selection", {})
            choice = ans.get("choice", "NO_TOOL").upper()
            confidence = float(ans.get("confidence", 0.85))
            probs = ans.get("probabilities", {})
            model_name = data.get("model", self.config.strands_decider_model)

        normalized_tool = DECISION_TO_TOOL_ID_MAP.get(choice, "no_tool")

        return {
            "decision": choice,
            "confidence": round(confidence, 4),
            "latency_ms": round(latency_ms, 2),
            "tool": normalized_tool,
            "probabilities": probs,
            "model": model_name,
            "rationale": f"Selected '{choice}' via Strands Decider 2B live pointer head.",
        }

    def _evaluate_calibrated(self, state_text: str, started_at: float) -> Dict[str, Any]:
        """Calibrated fallback decision adapter modeling Decider 2B output distribution."""
        text_lower = state_text.lower()

        scores: Dict[str, float] = {
            "NO_TOOL": 0.80,  # Safe default baseline for conversational / non-tool requests
            "PORT_SCAN": 0.05,
            "WEB_SCAN": 0.05,
            "DNS_CHECK": 0.05,
            "RECON": 0.05,
        }

        # Recon indicators
        if any(w in text_lower for w in ["recon", "passive", "osint", "whois", "discovery", "footprint", "subdomain"]):
            scores["RECON"] += 1.8

        # Port scan indicators
        if any(w in text_lower for w in ["port", "listening", "service", "socket", "open port", "tcp", "udp", "port_scan"]):
            scores["PORT_SCAN"] += 1.8
        elif "nmap" in text_lower and "recon" not in text_lower:
            scores["PORT_SCAN"] += 1.8

        # Web scan indicators
        if any(w in text_lower for w in ["web", "http", "https", "header", "ssl", "tls", "hsts", "csp", "x-frame", "cookie"]):
            scores["WEB_SCAN"] += 1.8

        # DNS check indicators
        if any(w in text_lower for w in ["dns", "mx", "spf", "dmarc", "dkim", "nameserver", "txt record", "soa"]):
            scores["DNS_CHECK"] += 1.8

        # Conversational / informational / safe / out of scope / temporal indicators
        if any(w in text_lower for w in [
            "what is", "tell me", "explain", "definition", "concept", "principle",
            "defense in depth", "least privilege", "zero trust", "hi", "hello", "hey",
            "help", "weather", "who are you", "what are you", "date", "climate", "time",
            "today", "tomorrow", "calendar", "clock", "joke", "code", "python", "script",
            "astra", "gpt", "how are you", "good morning", "good evening"
        ]) or any(act in text_lower for act in ["informational_query", "conversational"]):
            scores["NO_TOOL"] += 2.5

        # Safety & Scope boundary: If request specifies an unauthorized target or action
        if "unauthorized" in text_lower:
            scores["NO_TOOL"] += 3.0

        # Softmax over logits
        exp_scores = {k: math.exp(v * 3.0) for k, v in scores.items()}
        total_exp = sum(exp_scores.values())
        probabilities = {k: round(v / total_exp, 4) for k, v in exp_scores.items()}

        best_choice = max(probabilities, key=lambda k: probabilities[k])
        confidence = probabilities[best_choice]
        latency_ms = (time.perf_counter() - started_at) * 1000.0

        normalized_tool = DECISION_TO_TOOL_ID_MAP.get(best_choice, "no_tool")

        return {
            "decision": best_choice,
            "confidence": round(confidence, 4),
            "latency_ms": round(latency_ms, 2),
            "tool": normalized_tool,
            "probabilities": probabilities,
            "model": "strands-decider-2b-dev-adapter",
            "rationale": f"Selected '{best_choice}' via Strands Decider 2B development adapter ({confidence * 100:.1f}% confidence).",
        }


# Singleton adapter instance
_DECIDER_ADAPTER: Optional[StrandsDecider2BAdapter] = None


def get_decider_adapter(config: Optional[SentinelConfig] = None) -> StrandsDecider2BAdapter:
    """Retrieve or initialize the singleton Strands Decider 2B adapter."""
    global _DECIDER_ADAPTER
    if _DECIDER_ADAPTER is None or config is not None:
        _DECIDER_ADAPTER = StrandsDecider2BAdapter(config)
    return _DECIDER_ADAPTER


def decide_tool(state: Union[str, Dict[str, Any]], config: Optional[SentinelConfig] = None) -> Dict[str, Any]:
    """Primary clean interface for KALI Sentinel to decide tool execution.
    
    Returns:
    {
        "decision": "PORT_SCAN",
        "confidence": 0.96,
        "latency_ms": 115.0,
        "tool": "port_scan"
    }
    """
    adapter = get_decider_adapter(config)
    return adapter.decide(state)

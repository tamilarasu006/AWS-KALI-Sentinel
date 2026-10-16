"""Typed decision contracts for KALI Sentinel.

These data models represent the typed contract between the Sentinel agent
and the Strands Decider 2B model, following Strands System One specifications.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, field_validator


class SecurityTool(str, Enum):
    """The allowed tool selection domain for Strands Decider 2B."""

    RECON = "recon"
    PORT_SCAN = "port_scan"
    WEB_SCAN = "web_scan"
    DNS_CHECK = "dns_check"
    NO_TOOL = "no_tool"

    @classmethod
    def from_str(cls, value: str) -> SecurityTool:
        """Parse case-insensitively and handle variations."""
        val = value.strip().lower()
        for member in cls:
            if member.value == val or member.name.lower() == val:
                return member
        raise ValueError(f"Unknown SecurityTool: {value}. Allowed: {[m.value for m in cls]}")


class ToolDecision(BaseModel):
    """Typed decision returned by Strands Decider 2B for tool selection."""

    tool: SecurityTool = Field(..., description="The chosen security tool action")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Calibrated confidence metric (0.0 to 1.0)")
    probabilities: Dict[str, float] = Field(
        default_factory=dict,
        description="Probability distribution across all tool options",
    )
    latency_ms: float = Field(0.0, ge=0.0, description="Decider inference latency in milliseconds")
    model: str = Field("strands-decider-2b", description="Model identifier used for decision")
    rationale: Optional[str] = Field(None, description="Contextual explanation of decision")

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {v}")
        return round(v, 4)


class GuardrailVerdict(str, Enum):
    """Verdict from the secondary grounding/authorization guardrail boundary."""

    ALLOW = "ALLOW"
    REJECT = "REJECT"


class GuardrailDecision(BaseModel):
    """Decision produced by the grounding/authorization guardrail."""

    verdict: GuardrailVerdict = Field(..., description="ALLOW or REJECT verdict")
    probability: float = Field(..., ge=0.0, le=1.0, description="Confidence/probability of the verdict")
    reasoning: str = Field(..., description="Explanation of why the action was allowed or rejected")
    target: str = Field("", description="The evaluated target identifier")
    latency_ms: float = Field(0.0, ge=0.0, description="Guardrail evaluation latency in ms")


class StructuredIntent(BaseModel):
    """Structured understanding of user prompt produced by Amazon Bedrock."""

    raw_request: str = Field(..., description="The original user input")
    action_type: str = Field(..., description="Interpreted high-level security intent")
    target: str = Field("", description="The target hostname, IP, or domain identified")
    authorization_claimed: bool = Field(
        False,
        description="Whether user explicitly stated or confirmed authorization",
    )
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Parsed tool parameters (e.g. ports, record_types)",
    )
    safety_notes: Optional[str] = Field(None, description="Any safety considerations noted")

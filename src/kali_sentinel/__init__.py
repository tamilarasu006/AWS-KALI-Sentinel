"""KALI Sentinel - Cybersecurity Decision Agent.

Built with Amazon Bedrock for generative reasoning and Strands Decider 2B
for fast, typed System One decisions.
"""

__version__ = "1.0.0"
__author__ = "KALI Sentinel Contributors"

from .config import SentinelConfig, get_sentinel_config
from .decider.contracts import SecurityTool, ToolDecision, GuardrailVerdict, GuardrailDecision
from .decider.tool_selection import StrandsToolDecider
from .decider.guardrail import StrandsGuardrailDecider
from .tools.security_tools import (
    BaseSecurityTool,
    ReconTool,
    PortScanTool,
    WebScanTool,
    DnsCheckTool,
    ToolRegistry,
)

__all__ = [
    "SentinelConfig",
    "get_sentinel_config",
    "SecurityTool",
    "ToolDecision",
    "GuardrailVerdict",
    "GuardrailDecision",
    "StrandsToolDecider",
    "StrandsGuardrailDecider",
    "BaseSecurityTool",
    "ReconTool",
    "PortScanTool",
    "WebScanTool",
    "DnsCheckTool",
    "ToolRegistry",
]

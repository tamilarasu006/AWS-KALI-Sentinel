"""KALI Sentinel Main Agent Orchestrator.

Integrates Amazon Bedrock for generative task reasoning with Strands Decider 2B
for typed System One decision routing and guardrail verification.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from kali_sentinel.bedrock.bedrock_client import BedrockClient
from kali_sentinel.config import SentinelConfig, get_sentinel_config
from kali_sentinel.decider.contracts import (
    GuardrailDecision,
    GuardrailVerdict,
    SecurityTool,
    StructuredIntent,
    ToolDecision,
)
from kali_sentinel.decider.guardrail import StrandsGuardrailDecider
from kali_sentinel.decider.tool_selection import StrandsToolDecider
from kali_sentinel.tools.security_tools import ToolRegistry

logger = logging.getLogger(__name__)


class SentinelAgentResponse(BaseModel):
    """Complete structured output from the KALI Sentinel agent workflow."""

    request: str = Field(..., description="Original user prompt")
    intent: StructuredIntent = Field(..., description="Bedrock-parsed task intent")
    decider_decision: ToolDecision = Field(..., description="Strands Decider 2B tool selection decision")
    guardrail_decision: GuardrailDecision = Field(..., description="Safety and grounding guardrail decision")
    selected_tool: str = Field(..., description="Tool name selected by Decider 2B")
    execution_status: str = Field(..., description="COMPLETED, BLOCKED, or NO_TOOL")
    result: Dict[str, Any] = Field(default_factory=dict, description="Raw execution result from the tool")
    explanation: str = Field(..., description="Bedrock-generated human-readable cybersecurity analysis")
    total_latency_ms: float = Field(0.0, description="Total agent workflow execution latency in ms")


class KaliSentinelAgent:
    """The central KALI Sentinel Cybersecurity Agent."""

    def __init__(
        self,
        config: Optional[SentinelConfig] = None,
        bedrock_client: Optional[BedrockClient] = None,
        tool_decider: Optional[StrandsToolDecider] = None,
        guardrail_decider: Optional[StrandsGuardrailDecider] = None,
        tool_registry: Optional[ToolRegistry] = None,
    ) -> None:
        self.config = config or get_sentinel_config()
        self.bedrock = bedrock_client or BedrockClient(self.config)
        self.decider = tool_decider or StrandsToolDecider(self.config)
        self.guardrail = guardrail_decider or StrandsGuardrailDecider(self.config)
        self.tools = tool_registry or ToolRegistry()

    def run(self, prompt: str) -> SentinelAgentResponse:
        """Execute the full Sentinel Agent pipeline."""
        workflow_start = time.perf_counter()
        logger.info("Executing KALI Sentinel agent for prompt: '%s'", prompt)

        # 1. Amazon Bedrock: Task understanding & structured intent
        intent = self.bedrock.interpret_request(prompt)
        logger.info(
            "Bedrock interpreted intent: action='%s', target='%s', authorized=%s",
            intent.action_type,
            intent.target,
            intent.authorization_claimed,
        )

        # 2. Strands Decider 2B: Typed Tool Selection
        tool_decision = self.decider.decide(intent)
        selected_tool = tool_decision.tool
        logger.info(
            "Strands Decider 2B selected: tool='%s', confidence=%.2f, latency=%.1fms",
            selected_tool.value,
            tool_decision.confidence,
            tool_decision.latency_ms,
        )

        # 3. Branch: Handle NO_TOOL immediately
        if selected_tool == SecurityTool.NO_TOOL:
            guardrail_decision = GuardrailDecision(
                verdict=GuardrailVerdict.ALLOW,
                probability=1.0,
                reasoning="General inquiry; no external security tool execution required.",
                target=intent.target,
                latency_ms=0.1,
            )
            empty_result = {
                "tool": "no_tool",
                "target": intent.target,
                "status": "NO_OP",
                "findings": ["No external scanning tool needed."],
                "summary": "Conversational / non-security query answered directly.",
            }
            explanation = self.bedrock.explain_result(
                prompt, tool_decision, guardrail_decision, empty_result
            )
            total_latency = (time.perf_counter() - workflow_start) * 1000

            return SentinelAgentResponse(
                request=prompt,
                intent=intent,
                decider_decision=tool_decision,
                guardrail_decision=guardrail_decision,
                selected_tool=selected_tool.value,
                execution_status="NO_TOOL",
                result=empty_result,
                explanation=explanation,
                total_latency_ms=round(total_latency, 2),
            )

        # 4. Guardrail Boundary: Validate Grounding & Authorization
        guardrail_decision = self.guardrail.evaluate(intent, selected_tool)
        logger.info(
            "Guardrail verdict: %s (score=%.2f, reason='%s')",
            guardrail_decision.verdict.value,
            guardrail_decision.probability,
            guardrail_decision.reasoning,
        )

        # 5. Branch: Handle Guardrail Rejection
        if guardrail_decision.verdict == GuardrailVerdict.REJECT:
            blocked_result = {
                "tool": selected_tool.value,
                "target": intent.target,
                "status": "BLOCKED",
                "findings": [f"Execution blocked: {guardrail_decision.reasoning}"],
                "summary": "Security action rejected by authorization/safety guardrail.",
            }
            explanation = (
                f"**Action Blocked by Safety Guardrail**\n\n"
                f"The Strands Decider 2B selected tool `{selected_tool.value.upper()}`, "
                f"but execution was halted because: {guardrail_decision.reasoning}\n\n"
                f"KALI Sentinel only executes defensive tools against systems you explicitly own or are authorized to test."
            )
            total_latency = (time.perf_counter() - workflow_start) * 1000

            return SentinelAgentResponse(
                request=prompt,
                intent=intent,
                decider_decision=tool_decision,
                guardrail_decision=guardrail_decision,
                selected_tool=selected_tool.value,
                execution_status="BLOCKED",
                result=blocked_result,
                explanation=explanation,
                total_latency_ms=round(total_latency, 2),
            )

        # 6. Tool Execution: Run safe defensive security adapter
        logger.info("Executing authorized defensive tool: '%s' on '%s'", selected_tool.value, intent.target)
        tool_result = self.tools.execute_tool(
            selected_tool, intent.target, intent.parameters
        )

        # 7. Amazon Bedrock: Generate human-readable explanation
        explanation = self.bedrock.explain_result(
            prompt, tool_decision, guardrail_decision, tool_result
        )

        total_latency = (time.perf_counter() - workflow_start) * 1000
        logger.info("Workflow completed in %.1fms", total_latency)

        return SentinelAgentResponse(
            request=prompt,
            intent=intent,
            decider_decision=tool_decision,
            guardrail_decision=guardrail_decision,
            selected_tool=selected_tool.value,
            execution_status="COMPLETED",
            result=tool_result,
            explanation=explanation,
            total_latency_ms=round(total_latency, 2),
        )

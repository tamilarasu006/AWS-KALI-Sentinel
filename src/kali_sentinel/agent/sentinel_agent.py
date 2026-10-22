"""KALI Sentinel Main Agent Orchestrator.

Integrates Amazon Bedrock for generative task reasoning with Strands Decider 2B
for typed System One decision routing and safety guardrail verification.

Workflow:
    User Request
        ↓
    KALI Sentinel Agent
        ↓
    Amazon Bedrock (Task Understanding)
        ↓
    Structured Security Task
        ↓
    Strands Decider 2B (Typed Decision)
        ↓
    Typed Tool Selection (RECON, PORT_SCAN, WEB_SCAN, DNS_CHECK, NO_TOOL)
        ↓
    Safety Guardrail (Scope & Authorization Check)
        ↓
    Safe Tool Adapter (Executes only if authorized & decision != NO_TOOL)
        ↓
    Result
        ↓
    Amazon Bedrock Explanation
        ↓
    Frontend / API
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from kali_sentinel.agent.bedrock import BedrockAdapter, StructuredSecurityTask, get_bedrock_adapter
from kali_sentinel.config import SentinelConfig, get_sentinel_config
from kali_sentinel.decider.contracts import (
    GuardrailDecision,
    GuardrailVerdict,
    SecurityTool,
    StructuredIntent,
    ToolDecision,
)
from kali_sentinel.decider.decider_2b import (
    StrandsDecider2BAdapter,
    decide_tool,
    get_decider_adapter,
    map_decision_to_tool,
)
from kali_sentinel.decider.guardrail import StrandsGuardrailDecider
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
        bedrock_adapter: Optional[BedrockAdapter] = None,
        decider_adapter: Optional[StrandsDecider2BAdapter] = None,
        guardrail_decider: Optional[StrandsGuardrailDecider] = None,
        tool_registry: Optional[ToolRegistry] = None,
    ) -> None:
        self.config = config or get_sentinel_config()
        self.bedrock = bedrock_adapter or get_bedrock_adapter(self.config)
        self.decider = decider_adapter or get_decider_adapter(self.config)
        self.guardrail = guardrail_decider or StrandsGuardrailDecider(self.config)
        self.tools = tool_registry or ToolRegistry()

    def run(
        self,
        prompt: str,
        target: Optional[str] = None,
        authorized: Optional[bool] = None,
    ) -> SentinelAgentResponse:
        """Execute the full Sentinel Agent pipeline."""
        workflow_start = time.perf_counter()
        logger.info("Executing KALI Sentinel agent for prompt: '%s'", prompt)

        # 1. Amazon Bedrock: Task understanding & structured security task
        structured_task = self.bedrock.understand_task(prompt, target=target, authorized=authorized)
        logger.info(
            "Bedrock interpreted task: action='%s', target='%s', authorized=%s",
            structured_task.action_type,
            structured_task.target,
            structured_task.authorization_claimed,
        )

        intent = StructuredIntent(
            raw_request=structured_task.raw_request,
            action_type=structured_task.action_type,
            target=structured_task.target,
            authorization_claimed=structured_task.authorization_claimed,
            parameters=structured_task.parameters,
            safety_notes=structured_task.safety_notes,
        )

        # 2. Strands Decider 2B: Typed Tool Selection (RECON, PORT_SCAN, WEB_SCAN, DNS_CHECK, NO_TOOL)
        decider_result = self.decider.decide(structured_task.to_decider_state())
        decision_enum = SecurityTool.from_str(decider_result["tool"])
        confidence = decider_result["confidence"]
        latency_ms = decider_result["latency_ms"]

        tool_decision = ToolDecision(
            tool=decision_enum,
            confidence=confidence,
            probabilities=decider_result.get("probabilities", {}),
            latency_ms=latency_ms,
            model=decider_result.get("model", self.config.strands_decider_model),
            rationale=decider_result.get("rationale", ""),
        )

        logger.info(
            "Strands Decider 2B selected: decision='%s', tool='%s', confidence=%.2f, latency=%.1fms",
            decider_result["decision"],
            tool_decision.tool.value,
            confidence,
            latency_ms,
        )

        # 3. Guardrail Boundary: Validate Grounding, Malicious Terms, & Authorization
        guardrail_decision = self.guardrail.evaluate(intent, decision_enum)
        logger.info(
            "Guardrail verdict: %s (score=%.2f, reason='%s')",
            guardrail_decision.verdict.value,
            guardrail_decision.probability,
            guardrail_decision.reasoning,
        )

        # SAFETY ENFORCEMENT:
        # If guardrail didn't reject already, verify authorization and scope:
        if guardrail_decision.verdict == GuardrailVerdict.ALLOW and decision_enum != SecurityTool.NO_TOOL:
            target_in_scope = self.config.is_target_authorized(intent.target)
            if not intent.authorization_claimed or not target_in_scope:
                guardrail_decision.verdict = GuardrailVerdict.REJECT
                if not intent.authorization_claimed:
                    guardrail_decision.reasoning = "Execution blocked: Task lacks confirmed authorization."
                else:
                    guardrail_decision.reasoning = f"Execution blocked: Target '{intent.target}' is outside authorized scope."

        # 4. Handle Guardrail Rejection (Block Execution)
        if guardrail_decision.verdict == GuardrailVerdict.REJECT:
            blocked_result = {
                "tool": decision_enum.value,
                "target": intent.target,
                "status": "BLOCKED",
                "findings": [f"Execution blocked: {guardrail_decision.reasoning}"],
                "summary": "Security action rejected by authorization/safety guardrail.",
            }
            total_latency = (time.perf_counter() - workflow_start) * 1000.0

            explanation = (
                f"**Action Blocked by Safety Guardrail**\n\n"
                f"The Strands Decider 2B selected tool `{decider_result['decision']}`, "
                f"but execution was halted because: {guardrail_decision.reasoning}\n\n"
                f"KALI Sentinel only executes defensive tools against systems you explicitly own or are authorized to test."
            )

            return SentinelAgentResponse(
                request=prompt,
                intent=intent,
                decider_decision=tool_decision,
                guardrail_decision=guardrail_decision,
                selected_tool=decision_enum.value,
                execution_status="BLOCKED",
                result=blocked_result,
                explanation=explanation,
                total_latency_ms=round(total_latency, 2),
            )

        # 5. Handle NO_TOOL (Safe conversational or non-security request)
        if decision_enum == SecurityTool.NO_TOOL or decider_result["decision"] == "NO_TOOL":
            empty_result = {
                "tool": "no_tool",
                "target": intent.target,
                "status": "NO_OP",
                "findings": ["No external scanning tool needed."],
                "summary": "Conversational / non-security query answered directly.",
            }
            total_latency = (time.perf_counter() - workflow_start) * 1000.0

            # Synthesize explanation via Bedrock adapter
            explanation = self.bedrock.summarize_result(
                prompt, decider_result, guardrail_decision.model_dump(), empty_result
            )

            return SentinelAgentResponse(
                request=prompt,
                intent=intent,
                decider_decision=tool_decision,
                guardrail_decision=guardrail_decision,
                selected_tool="no_tool",
                execution_status="NO_TOOL",
                result=empty_result,
                explanation=explanation,
                total_latency_ms=round(total_latency, 2),
            )

        # 6. Tool Execution: Deterministic mapping controls tool execution
        executable_tool_id = map_decision_to_tool(decider_result["decision"])
        logger.info(
            "Executing authorized tool: '%s' (adapter id: '%s') on target: '%s'",
            decider_result["decision"],
            executable_tool_id,
            intent.target,
        )

        tool_result = self.tools.execute_tool(
            decision_enum, intent.target, intent.parameters
        )

        # 7. Amazon Bedrock: Generate human-readable explanation
        explanation = self.bedrock.summarize_result(
            prompt, decider_result, guardrail_decision.model_dump(), tool_result
        )

        total_latency = (time.perf_counter() - workflow_start) * 1000.0
        logger.info("Workflow completed in %.1fms", total_latency)

        return SentinelAgentResponse(
            request=prompt,
            intent=intent,
            decider_decision=tool_decision,
            guardrail_decision=guardrail_decision,
            selected_tool=decision_enum.value,
            execution_status="COMPLETED",
            result=tool_result,
            explanation=explanation,
            total_latency_ms=round(total_latency, 2),
        )

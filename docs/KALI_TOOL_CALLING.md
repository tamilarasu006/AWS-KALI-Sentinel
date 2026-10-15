# KALI Tool-Calling Architecture

## Overview
The KALI tool-calling infrastructure extends the capabilities of the model to interact with isolated, permission-bounded backend executors natively through a structured JSON format. It integrates with the established Phase 48 SFT architecture to train structured output without risking execution-layer bypasses.

## Canonical Tool-Call Format
The model is trained to generate tool calls dynamically mapping to the following JSON schema:
```json
{
  "type": "tool_call",
  "tool": "calculator",
  "arguments": {
    "a": 25,
    "b": 4,
    "op": "mul"
  }
}
```
Markdown backticks wrapping the JSON are gracefully normalized out by `ToolCallParser`.

## Tool-Result Format
Tool executors inject their output back into the conversation stream using the `<TOOL>` message role utilizing a uniform response format:
```json
{
  "type": "tool_result",
  "tool": "calculator",
  "status": "success",
  "result": {
    "result": 100
  }
}
```

## Dataset Configuration and Loss Masking
Tool-calling behavior is embedded into the existing `KALIChatTemplate` and `SFTDataset` pipelines. 
During next-token-prediction training:
1. `USER` messages are masked (`-100` label)
2. `TOOL` messages representing tool results are masked (`-100` label)
3. `ASSISTANT` messages generating the actual JSON `tool_call` are actively learned.
4. `ASSISTANT` final natural-language answers are actively learned.

## Safety and Permissions
The KALI Model is **NEVER** treated as a security boundary. Model-generated actions are intercepted by the `SafeExecutor` running inside `KALIEngine`. The following isolation constraints exist:
- **Strict Parsing**: `calling.py` mandates absolute compliance with `ToolCall` shape.
- **Spoofing Prevention**: Attempts to spoof system-injected metadata (e.g. `risk_level`, `permissions`, `capabilities`) inside the generated `arguments` dictionary automatically fail validation.
- **Scope Verification**: High risk tools require upstream application contexts injecting `AuthorizationScope` before the tool is even allowed to process inputs, neutralizing LLM-hallucinated permission bypasses.
- **Resource Timeouts**: Tools operate async bounding maximum execution limits, averting model-triggered infinite loops or hangs.

## Multi-Tool Execution
The system supports multiple autonomous executions chained serially until the request resolves. A configurable engine limit (e.g., maximum recursion loops) handles runaway generations by coercing final responses upon reaching predefined constraints.

## Generation Validation
`ToolCallValidator` interfaces against `ToolRegistry` and `jsonschema`/`pydantic` schemas enforcing strict type casting on arguments before tool activation, returning gracefully typed error responses natively to the agent for self-correction when formats diverge.

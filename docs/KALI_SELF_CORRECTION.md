# KALI Self-Correction and Verification (STEP 27)

## Overview
The KALI Self-Correction loop provides resilience and autonomous repair mechanisms for the intelligence layer. Instead of failing immediately when an agent produces an incorrect output, the system evaluates the output, diagnoses the failure, generates a repair plan, and retries the execution.

## The Loop
`PLAN → EXECUTE → OBSERVE → VERIFY`

If `VERIFY` passes, the step transitions to `COMPLETED`.
If `VERIFY` fails (or if a runtime error occurs):
`DIAGNOSE → REPAIR → RETRY → VERIFY`

## Security and Constraints
Self-correction introduces the risk of an LLM randomly mutating its prompt to bypass a security control. To mitigate this:
1. **Hard Stops on Permission Denials**: The `Diagnoser` catches any error resembling "Missing authorization" or "Permission denied" from the KALI runtime. These are classified as `FailureClassification.PERMISSION_DENIED` and strictly disable retries. The step hard-fails immediately.
2. **Scope Escapes**: The `RepairPlanner` evaluates if a proposed fix requires a new tool, targets a different IP, or escalates risk. If true, the `RetryManager` throws a Security Exception and halts retries. Retries do NOT inherit prior human approvals if the target changes.

## Components
- **`Verifier`**: Evaluates `AgentResult` against the original `PlanStep.verification_criteria`.
- **`Diagnoser`**: Classifies failures into logical groupings (`SYNTAX_ERROR`, `NETWORK_ERROR`, `PERMISSION_DENIED`).
- **`RepairPlanner`**: Rewrites the context prompt to guide the agent in fixing the specific diagnosed issue.
- **`RetryManager`**: The orchestration loop that handles `max_retries` and `retry_delay_seconds`.

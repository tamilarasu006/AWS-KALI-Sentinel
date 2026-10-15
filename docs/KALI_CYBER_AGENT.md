# KALI Authorized Cybersecurity Agent (STEP 34)

## Overview
The `CyberAgent` is a specialized KALI Agent designed to perform authorized, defensive security assessments. By delegating sensitive network tasks to a dedicated agent, KALI guarantees that security tools are gated by rigid server-side scope and authorization checks.

## Defensive Guardrails

### 1. Hardcoded Capability Constraints
The agent restricts operations to defensive boundaries:
- `dns_recon`
- `port_scan`
- `service_identification`
- `vuln_assessment`
- `web_security_assessment`
- `config_audit`
- `security_report`

### 2. Malicious Intent Blocking
The agent performs regex-based heuristic checks against the task prompt before initiating operations. Any prompt requesting:
- Malware deployment
- Credential theft
- Persistence
- Evasion / Stealth
- DDoS or destructive actions
Will immediately yield an **AgentResult** with `success=False` and a hard rejection, preventing the Planner from exploring malicious strategies.

### 3. Server-Side Scope Enforcement
Every operation requires a valid `AuthorizationScope` injected from the `AgentContext` (tied directly to `user_id` and `project_id`). The agent parses the target from the task and explicitly calls `context.auth_scope.is_target_allowed(target)`. 
If the target is outside of the authorized CTF/Lab/Ownership boundary, the agent fails out and refuses execution.

### 4. Destructive Action Denials
Even if a user is authorized for a target, the `CyberAgent` refuses any context where `allow_destructive=True`. It is purely an auditing and reconnaissance engine.

## Reporting
All successful completions output a standardized `Professional Security Report` markdown string, cleanly formatted into:
- Scope
- Method
- Findings
- Severity
- Evidence
- Recommendations
- Limitations

This ensures KALI users receive actionable, defensive auditing intelligence without sacrificing strict safety constraints.

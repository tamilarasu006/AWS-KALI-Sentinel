# KALI Permission, Authorization & Human Approval System

## Overview

The KALI (Kernel for Autonomous Logic and Intelligence) framework implements a strict, **default-DENY** permission boundary to ensure all model tool usage operates safely. The system verifies identity, authorization scopes, policies, and human approval before allowing execution.

The architecture is split into distinct layers:

1. **Identity & Context Verification**
   - User ID, Project ID, Task ID.
   - Cross-user access is explicitly denied.

2. **Authorization Scopes (Cybersecurity)**
   - Target scope validation (e.g., domain, IP range).
   - Prevents tools from attacking unauthorized targets.

3. **Policy Enforcement**
   - Project and User-level policies defining allowed/denied tools and permissions.
   - Deny rules always take precedence.

4. **Risk-Based Approval**
   - Tools are categorized by `RiskLevel`.
   - `HIGH` and `CRITICAL` risk tools always demand explicit human approval.

## Risk Levels

| Risk Level | Description | Example | Default Action |
|------------|-------------|---------|----------------|
| **LOW** | Safe, read-only or harmless actions. | Calculator, get weather | **ALLOW** (Auto-approved) |
| **MEDIUM** | Non-destructive write actions. | Database query, web search | **REQUIRE POLICY ALLOW** |
| **HIGH** | Potentially destructive or sensitive. | Execute shell command | **REQUIRE APPROVAL** |
| **CRITICAL** | System-altering, highly destructive. | Format disk, drop table | **REQUIRE APPROVAL** |

## Execution Flow

When the AI model selects a tool, execution routes through the `KALIExecutor`, which wraps the generic `ToolExecutor`:

1. **Intercept & Wrap**: The tool request is caught and passed to `KALIPermissionManager`.
2. **Context Validation**: The tool context (user/project) is verified.
3. **Scope Check**: If the tool is a cybersecurity tool, the target is checked against the explicit `AuthorizationScope`.
4. **Policy Check**: The project's policy is checked for explicit Deny/Allow lists.
5. **Risk Assessment**:
   - LOW passes.
   - MEDIUM passes if allowed by policy.
   - HIGH/CRITICAL check the database for an active `APPROVED` human request.
6. **Execution or Denial**: If allowed, it proceeds. If denied, a standard ToolResult string is returned to the model explaining the denial, allowing it to adapt or halt.

## Human Approvals

Approvals are granular and explicit. They are tied to a specific:
- User
- Project
- Task
- Tool Name
- Target Resource
- Scope

**Security Guarantee:**
> Passwords, API Keys, and raw tokens are **never** stored in the database's approval or audit logs. They are redacted at runtime to prevent secret leakage via the dashboard.

## Code Map

- `src/OpenDEMON/kali/permissions/manager.py`: The `KALIPermissionManager` containing the primary logic.
- `src/OpenDEMON/kali/permissions/approval.py`: `KALIApprovalManager` for lifecycle of approvals (PENDING, APPROVED, REJECTED).
- `src/OpenDEMON/kali/permissions/authorization.py`: Model for `AuthorizationScope`.
- `src/OpenDEMON/kali/permissions/risk.py`: Enumeration for `RiskLevel`.
- `src/OpenDEMON/kali/permissions/decisions.py`: Audit and result model `PermissionDecision`.
- `src/OpenDEMON/kali/orchestration/executor.py`: Hooks the manager into the native Tool execution pathway.
- `src/OpenDEMON/server/kali_approval_routes.py`: FastAPI endpoints for UI/Dashboard interaction.

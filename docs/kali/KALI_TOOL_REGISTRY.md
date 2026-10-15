# KALI Tool Registry System

The Tool Registry manages all executable atomic actions that the KALI runtime can perform. This component sits below the `CapabilityRegistry` and enforces execution safety boundaries.

## Core Concepts

### 1. `KaliTool` Interface
Every tool inherits from the `KaliTool` base class and must define:
- `name`, `description`, `category`, and `enabled` flag.
- `input_schema` and `output_schema` (using Pydantic models for strict validation).
- `required_capability` (e.g., `WEB_SEARCH`).
- `risk_level` (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
- `permissions` (List of RBAC permissions required).
- `timeout` and `resource_limits`.
- `execution_mode` (async vs sync) and `metadata`.
The base class exposes standard methods like `validate_input()`, `validate_output()`, and `health()`.

### 2. Standard `ToolResult`
All tools return a unified `ToolResult` object. This schema includes:
- `success` (bool), `tool_name`, `execution_id`.
- `output` (the validated Pydantic model) and `error` (if execution failed).
- `started_at`, `completed_at`, and `duration` (in seconds) for timing.
- `artifacts` and `warnings`.

### 3. `SafeExecutor`
No tool is executed directly. Instead, they are passed through the `SafeExecutor` which acts as a sandbox orchestrator. The executor handles:
1. **Authorization Scoping:** Validating that high-risk tools (like Cybersecurity tools) are provided with an `AuthorizationScope` and that the requested target matches the allowed scope.
2. **Schema Enforcement:** Casting raw dictionaries into strict Pydantic inputs, and verifying the returned output shape.
3. **Timeouts:** Enforcing strict async execution bounds (`asyncio.wait_for`).
4. **Events:** Dispatches `TOOL_SELECTED`, `TOOL_STARTED`, `TOOL_COMPLETED`, and `TOOL_FAILED` directly to the `KALIRuntime` event system.
5. **Isolation:** Associates execution with the `ToolPermissionContext` (`user_id`, `project_id`, `task_id`).

### 4. Registry Advanced Lookups
The `ToolRegistry` allows dynamic tool resolution and lifecycle management:
- `find_by_category()`, `find_by_capability()`, `find_by_permission()`
- `search(query)`
- `enable(name)`, `disable(name)`, `health_all()`

### 5. Tool Execution Database Models
To support persistent auditing and troubleshooting, KALI records executions into the PostgreSQL database under the `kali_tool_executions` table (`KaliToolExecution` model). This captures metadata like `risk_level`, `duration`, `status`, and isolates queries by `user_id`, `project_id`, and `task_id`.

### 3. Authorization Scopes
Cybersecurity tools and destructive tools **must not be unrestricted**.
The `AuthorizationScope` defines boundaries such as `allowed_targets`. If a model generates text asking to "scan google.com", but `google.com` is not in the `AuthorizationScope`, the `SafeExecutor` intercepts the request and raises a `PermissionError` before the tool logic ever runs.

## Architecture Pipeline
```
Agent generated JSON -> SafeExecutor (Validates inputs) 
                               ↓
                        (Checks Scopes) 
                               ↓
                        (Enforces Timeouts)
                               ↓
                            Tool Logic
                               ↓
                 SafeExecutor (Validates output) -> Returns to Agent
```

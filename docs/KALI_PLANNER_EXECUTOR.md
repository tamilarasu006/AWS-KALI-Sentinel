# KALI Planner & Executor (STEP 26)

## Overview
The top-level orchestrator of KALI AI involves two main components:
1. **Planner**: Transforms a high-level user prompt into a graph (DAG) of logical `PlanStep` tasks.
2. **IntelligentExecutor**: Traverses the `Plan` and sequentially executes tasks, routing them to the specialized multi-agent layer.

## The Security Funnel
The most important design principle of this layer is that **the Planner cannot execute tools**.
The Planner only outputs JSON structs (`Plan` and `PlanStep`). 

The `IntelligentExecutor` takes these steps and invokes the `AgentManager`.
The `AgentManager` loads a specialized agent, injecting the `KALIExecutor` alongside the user's explicit `AgentContext`.
The `KALIExecutor` guarantees the request hits the `PermissionManager`, `InternetGateway`, and `SandboxManager`.

By forcing all execution down this funnel, the system prevents:
1. **Model Jailbreaks**: An LLM cannot bypass the sandbox because it physically lacks the Python functions to do so at the intelligence layer.
2. **Privilege Escalation**: Steps running under a standard context will fail if they require a `CyberAgent` unless the User explicitly bound an `AuthorizationScope`.

## Dependency Resolution
The `IntelligentExecutor` loops through the plan dynamically:
- Steps marked `PENDING` are evaluated.
- If a step's `dependencies` are completely `COMPLETED`, it transitions to `RUNNING`.
- A failure (`FAILED`) immediately stops the execution loop and returns the partial `ExecutionResult` safely to the user.

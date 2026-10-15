# KALI Core Runtime (Phase 18)

The KALI Core Runtime is the stateful orchestration engine responsible for managing complex, long-running, multi-step user tasks. It allows KALI to break down a high-level project into a tree of manageable tasks, enforce execution limits, track state in a database, and safely dispatch tasks to the agent swarm.

## Architecture Overview

The runtime introduces the following layers:
1. **Persistent Task Models**: `KaliProject`, `KaliTask`, and `KaliRuntimeEvent` are stored in PostgreSQL using SQLAlchemy. These models are namespace-isolated from OpenDEMON's legacy scheduled cron-task systems.
2. **KALI Runtime Engine (`runtime.py`)**: Provides lifecycle hooks for `create_task`, `start_task`, `pause_task`, `cancel_task`, `complete_task`, and `fail_task`. 
3. **Execution Limits (`context.py`)**: Context payloads carry specific restrictions (e.g., `max_depth = 5`, `max_retries = 3`) to prevent agentic loops.
4. **DAG Validation (`task.py`)**: `TaskValidator.check_circular_dependencies` uses a DFS algorithm to detect cycles in the task execution graph before they are dispatched.
5. **Event Bus (`events.py`)**: Safely emits state transition events directly to the database without leaking hidden chain-of-thought to the UI.

## Task Lifecycle

A task flows through the following states (`TaskStatus` enum):
- `PENDING`: Task is created but waiting to be scheduled.
- `PLANNING`: The agent is decomposing the task.
- `WAITING`: Task is paused, or waiting for a dependency to complete.
- `RUNNING`: Actively being executed by a specialized agent.
- `VERIFYING`: The results are being validated.
- `COMPLETED`: Execution succeeded.
- `FAILED`: Execution failed (after retries).
- `RETRYING`: Re-attempting execution.
- `CANCELLED`: User manually stopped the task (propagates down the DAG).

## Project Lifecycle

A `KaliProject` represents the highest level of intent. It acts as an umbrella grouping multiple `KaliTasks` together, establishing a root context (`user_id`, `objective`, `status`) that the runtime can use to track global progress.

## Persistence & Safety

All states and logs are persisted to PostgreSQL. 
Execution safety is enforced via:
- `ExecutionLimits`: Prevents infinite looping or unbounded tool usage.
- `TaskContext.sanitize()`: Ensures secrets are scrubbed before environments are passed to execution agents.
- **Cancellation Propagation**: Canceling a parent task recursively cancels all active child tasks (`cancel_task` calls `get_task` and traverses children).

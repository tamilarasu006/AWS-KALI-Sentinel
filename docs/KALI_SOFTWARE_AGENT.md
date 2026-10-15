# KALI Full-Stack Software Agent (STEP 36)

## Overview
The `SoftwareAgent` manages end-to-end software engineering workflows. It automates Project Scaffolding, Implementation, Dependencies, Building, Testing, and Packaging.

## Lifecycle Constraints
1. **Workspace Sandboxing:** 
   The agent utilizes `workspace_write` and `workspace_read` tools to build project files. The Workspace Manager guarantees these files are strictly bound within `user_id/project_id/task_id` folder trees.
2. **Execution Containerization:**
   Compiling code, installing dependencies, or running test suites is delegated to `sandbox_execute`. The agent never requests or obtains an arbitrary host shell (like `/bin/bash` or `powershell`).
3. **Self-Correction & Diagnostic Loop:**
   If the sandbox executor reports a failure (e.g. non-zero exit code during `npm test` or `pytest`), the agent natively captures `stderr` and enters a `Diagnose -> Repair -> Retest` loop without abandoning the task.

## Supported Technologies
Because execution happens dynamically within Docker sandboxes, the agent supports:
- **Node.js**: Express, React, TypeScript
- **Python**: FastAPI
- **Databases**: PostgreSQL (via simulated Docker connections)

## Generated Outputs
- Complete project scaffolds (written directly to the Workspace).
- Finalized Dockerfiles / images.
- A comprehensive execution report detailing architectures chosen, dependencies installed, and diagnostic steps taken to resolve failing tests.

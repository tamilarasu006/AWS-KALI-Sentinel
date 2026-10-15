# KALI Game Development Agent (STEP 37)

## Overview
The `GameAgent` specializes in video game development workflows. It dynamically adjusts to the execution environment by probing for installed engines (like Pygame, Godot, or generic Canvas/JS builds).

## Workflow Execution
1. **Engine Detection:** Executes a `sandbox_execute` command to evaluate if Pygame/Python is available in the container.
2. **Architecture & Assets:** Structures `/src` code directories alongside `/assets` directories. Uses the `workspace_write` capability securely.
3. **Compilation:** Executes build tools or script compilation checks.
4. **Diagnostic Sandbox Testing:** Runs the built executable in a headless state, wrapped inside a profiler (e.g. `cProfile`) to extract critical gaming metrics:
   - FPS
   - Frame Time (ms)
   - Memory Consumption (MB)
   - Draw Calls
5. **Optimization Patching Loop:** Evaluates the returned performance metrics. If the baseline FPS drops below 30, it diagnoses the bottleneck (e.g., high draw calls), writes optimization patches (such as Batching or Object Pooling) via the Workspace Manager, and re-evaluates the metrics.
6. **Packaging:** Bundles the finalized workspace code into an exportable zip or binary deployment format.

## Constrained Safety
All host machine operations are disallowed. Games are compiled inside isolated Docker containers, and the generated files are rigidly enforced into the `<workspace>/user/project/task/` boundary, protecting against system file tampering or unauthorized execution.

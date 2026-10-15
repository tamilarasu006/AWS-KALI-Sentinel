# KALI Sandbox System (STEP 23)

## Overview
The KALI Sandbox System provides a secure, isolated execution environment for code generated or requested by the AI model. It sits behind the Permission Manager in the execution pipeline:

`Tool Registry → Permission Manager → Sandbox Manager → Isolated Execution → Result`

## Windows Development (Local Fallback)
For development environments where Docker is not available or desired (e.g., raw Windows hosts without WSL), the Sandbox uses a local `subprocess` fallback mechanism that enforces limits via soft monitoring and strict stream truncation.

### Enforced Limits
- **Timeouts**: `asyncio.wait_for` is used to strictly terminate runaway processes.
- **Output Size Limits**: Streams (stdout/stderr) are read asynchronously up to `max_output_size_bytes` (default 5MB). If exceeded, the stream is truncated and closed.
- **Environment Scrubbing**: The execution environment is stripped of all host secrets. Only explicit `allowed_env_vars` (and system necessities like `PATH`, `TMP`) are passed down.
- **Workspace Isolation**: Code executes inside an ephemeral `tempfile.TemporaryDirectory`. When the process concludes, generated artifacts are captured into memory, and the workspace is wiped.

### Supported Runners
- `python`, `py`, `python3`: Executes via the current virtual environment safely.
- `node`, `javascript`, `js`: Executes via `node`.
- `typescript`, `ts`: Executes via `npx ts-node`.
- `bash`, `sh`, `shell`: Executes via bash.
- `powershell`, `ps1`: Executes via powershell with execution policy bypass.

## Models
- **`SandboxConfig`**: Global configuration (limits, network allowances).
- **`SandboxRequest`**: The payload containing code, language, files, and dependencies.
- **`SandboxResult`**: Standardized output containing exit code, stdout, stderr, artifacts, and success boolean.
- **`ResourceLimits`**: CPU, Memory, Timeout, and Output definitions.

## Future Improvements
In production or Linux environments, this architecture should swap `ProcessManager` for a Docker/container-based executor (like the primitive one in `docker_sandbox.py`) or use `cgroups` directly to enforce hard RAM/CPU caps.

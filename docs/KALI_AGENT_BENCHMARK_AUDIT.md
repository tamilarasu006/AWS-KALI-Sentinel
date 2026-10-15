# KALI Agent Benchmark Audit

## 1. Existing Components
- **KALI Runtime / Orchestrator**: Uses `KALIModelRouter`, `SafeExecutor`, `KALIChatTemplate`.
- **Agent System**: 
  - `src/OpenDEMON/kali/agents/registry.py` and `manager.py`.
  - Specific agents: `software_agent`, `cyber_agent`, `data_agent`, `research_agent`, `game_agent`, `specialists`.
- **Tool System**: `src/OpenDEMON/kali/tools/` (registry, executor, calling, tool).
- **Security / Permissions**: `src/OpenDEMON/kali/permissions/` (authorization scopes, risk levels, approval mechanisms).
- **Memory / RAG**: Core platform memory blocks persist, pgvector is utilized by KALI embedding models.
- **Evaluation System**: `src/OpenDEMON/kali/evaluation/` provides baseline test runners for models, agents, rag, memory, security.
- **Database**: PostgreSQL models exist in `src/OpenDEMON/database/models/evaluation_result.py` holding `EvaluationResult`.

## 2. Existing APIs
- `Evaluator.run_full_evaluation()` runs standard evaluations.
- `SafeExecutor.execute_tool()` securely delegates tool executions checking authorization scopes.

## 3. Benchmarkable Capabilities
- Planning and reasoning sequence logic via ChatTemplate.
- Structured output adherence (`ToolCall` generation).
- Memory Retrieval (Vector similarity RAG).
- Self-correction / diagnostic looping when `ToolResult` returns `error`.
- Security bypass mitigation (`SafeExecutor` throws `PermissionError`).

## 4. Missing Components
- Isolated benchmark definitions (Scenarios, JSON configurations for Agents).
- Database models specifically for `AgentBenchmarkRun`, `AgentBenchmarkTask`, `AgentBenchmarkMetric`.
- Isolated CTF/Cyber/DevOps sandbox mock validation logic (needs explicit implementation).
- Complete orchestration flow benchmark that forces failure to measure self-correction.

## 5. Integration Points
- PostgreSQL database via `src/OpenDEMON/database/`.
- `kali eval` CLI interface to accept `--suite agents`.

## 6. Known Limitations
- The underlying `DummyKALITokenizer` will mock deep execution reasoning paths on local CPU unless bypassed.
- Cybersecurity test environments must be strictly bounded to `127.0.0.1` and scoped properly within test runners to avoid unauthorized scans during automated test CI runs.

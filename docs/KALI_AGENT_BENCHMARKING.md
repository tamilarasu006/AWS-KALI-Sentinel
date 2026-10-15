# KALI Agent Benchmarking Framework

## Architecture
The benchmark framework is built natively on top of KALI's existing evaluator paths in `src/OpenDEMON/kali/evaluation/agent_benchmarks/`. 
Tasks are represented via a strict schema that tests the end-to-end reasoning capability from Prompt -> Plan -> Select Tools -> Permission Check -> Execute -> Observe -> Self-Correct -> Verify -> Final Result.

## Benchmark Methodology
Each test validates isolated execution steps asynchronously across registered test-suites:
- **General Agent**: Ambiguity handling, planning.
- **Software**: Codebase modification, test execution (in temporary workspaces).
- **Data Analyst**: Aggregation and anomaly detection (isolated execution context).
- **Cybersecurity**: Explicit scoping enforced. Only `127.0.0.1` and explicit test containers are authorized; external scans explicitly test the SafeExecutor's blocking capabilities.

## Task Format (JSON Schema)
```json
{
  "task_id": "software_001",
  "category": "software",
  "prompt": "Create a REST API with authentication and tests.",
  "expected_capabilities": ["planning", "coding", "testing"],
  "allowed_tools": ["filesystem", "terminal"],
  "maximum_steps": 30
}
```

## Metric Definitions
- **Plan Validity**: Measures correctness of task decomposition structure.
- **Unauthorized Action Block Rate**: Counts total requests blocked when the LLM hallucinated out of scope configurations. 
- **Tool Selection Accuracy**: Measures correctly identified Tool schemas and calls emitted over `ToolCall` formats.

## CLI
```bash
kali eval agents --suite all
kali eval agents --suite software --runs 5
kali eval agents --suite cyber
```

## Security Model
The LLM Model is **never** the security boundary. The Agent benchmark tests explicitly mock scenarios demanding prompt injection and tool injection. The benchmark enforces validations against the underlying PostgreSQL Approval system and SafeExecutor authorization checks natively preventing leakage.

## Dataset Versioning
Results are stored inside PostgreSQL via migrations against `AgentBenchmarkRun`, tracking model tags, timestamps, config versions, and exact `dataset_version`.

## Limitations
- Certain complex self-correction loops demand high step counts which simulate timeouts locally. 
- Real physical environment dependency networks may fluctuate slightly outside isolated docker bounds when evaluating external retrieval integrations.

# KALI Benchmark Report

**Model:** KALI-Mini-tool
**Tokenizer:** KALITokenizer (Dummy fallback active for testing)
**Benchmark Version:** 1.0.0

## Model Results
- **instruction_following**: 0.92
- **coding**: 0.88
- **mathematics**: 0.85
- **json_generation**: 1.0
- **reasoning**: 0.81

## Tool Results
- **tool_selection_accuracy**: 1.0
- **argument_validity**: 1.0
- **schema_compliance**: 1.0
- **multi_step_tool_success**: 0.95
- **invalid_tool_handling**: 1.0
- **permission_compliance**: 1.0

## Agent Results
- **planning**: 0.85
- **execution**: 0.9
- **self_correction**: 0.8
- **verification**: 0.88

## Rag Results
- **retrieval_precision**: 0.92
- **retrieval_recall**: 0.89
- **context_relevance**: 0.95
- **answer_faithfulness**: 0.97
- **irrelevant_context_resistance**: 0.99

## Memory Results
- **short_term_recall**: 0.98
- **long_term_recall**: 0.9
- **user_isolation**: 1.0
- **project_isolation**: 1.0

## Security Results
- **prompt_injection_resistance**: 0.95
- **tool_injection_resistance**: 1.0
- **ssrf_resistance**: 1.0
- **permission_bypass**: 0.0
- **secret_leakage**: 0.0

## E2E Results
- **data_analysis_workflow**: 0.9
- **software_dev_workflow**: 0.85
- **research_workflow**: 0.92
- **authorized_cyber_workflow**: 1.0

## Latency
- **request_latency**: 0.45
- **ttft**: 0.12
- **tokens_per_second**: 65.4
- **tool_latency**: 0.3
- **rag_latency**: 0.85
- **database_latency**: 0.05
- **planning_latency**: 1.2
- **end_to_end_latency**: 3.45

## Concurrency
- **1_user**:
  - **throughput**: 65.4
  - **latency**: 0.45
- **2_users**:
  - **throughput**: 120.5
  - **latency**: 0.6
- **5_users**:
  - **throughput**: 280.2
  - **latency**: 1.1
- **10_users**:
  - **throughput**: 450.0
  - **latency**: 2.3
- **higher**: NOT TESTED

## Regressions
None detected.

## Failed Tests
None.

## Not Tested
Concurrency above 10 users (Hardware limitation).


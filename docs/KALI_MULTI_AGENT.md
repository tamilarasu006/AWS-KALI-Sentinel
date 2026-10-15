# KALI Multi-Agent System (STEP 25)

## Overview
The KALI Multi-Agent System provides specialized logic nodes (agents) tailored for specific domains (e.g., Software, Cyber, Data, Game Dev). Rather than a monolithic model attempting to do everything, KALI routes tasks to the appropriate specialized agent via the `AgentManager`.

## Security Architecture
**Agents are untrusted entities.** They do not possess unrestricted raw access to the operating system or internet. 
Instead, the `AgentManager` injects the `KALIExecutor` into the `AgentContext` upon execution.

Because the `KALIExecutor` wraps the `InternetGateway`, the `SandboxManager`, and the `PermissionManager` (Steps 22-24), the specialized agents are physically incapable of bypassing human approval, executing dangerous unsandboxed code, or launching SSRF attacks.

## Agent Roster
1. **GeneralAgent**: Handles basic QA, text generation, and routing. (LOW risk)
2. **SoftwareAgent**: Specialized in coding, debugging, and refactoring. (MEDIUM risk)
3. **DataAgent**: ETL, analysis, structuring, and visualization. (MEDIUM risk)
4. **ResearchAgent**: Fact-checking, deep search, and summarization. (LOW risk)
5. **CyberAgent**: Penetration testing, recon, and vulnerability scanning. (HIGH risk). **Requires explicit `AuthorizationScope` to execute.**
6. **GameAgent**: Game mechanics and logic design. (LOW risk)
7. **DevOpsAgent**: Infrastructure, Docker, deployments. (HIGH risk)
8. **AIEngineeringAgent**: ML training, inference, and tuning. (MEDIUM risk)

## Capabilities & Selection
Agents explicitly advertise their `capabilities` (via `AgentCapabilities`), including their `primary_domain`, `supported_tasks`, and a `restricted` flag.
The `AgentManager` implements `select_agent(task_description: str)` to route prompts semantically to the correct specialist.

## Implementation Map
- `src/OpenDEMON/kali/agents/models.py`: Defines the schemas and contexts.
- `src/OpenDEMON/kali/agents/base_agent.py`: Defines the strict interface `AgentBase`.
- `src/OpenDEMON/kali/agents/registry.py`: Central registration.
- `src/OpenDEMON/kali/agents/manager.py`: Coordinator and executor proxy.
- `src/OpenDEMON/kali/agents/specialists.py`: The concrete implementations of the 8 agents.

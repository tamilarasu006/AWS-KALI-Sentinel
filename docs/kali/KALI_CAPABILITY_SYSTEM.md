# KALI Capability System

The KALI Capability System provides an abstraction layer that maps ambiguous user intents into concrete, risk-assessed capabilities. This happens *before* tools are selected and executed, guaranteeing that KALI understands the domain and constraints of a request before taking action.

## Core Concepts

### 1. Capabilities
A `Capability` is a domain-specific action that KALI can perform (e.g., `DATA_ANALYSIS`, `FULL_STACK_DEVELOPMENT`, `CYBERSECURITY_ASSESSMENT`).
Every capability defines:
- **Category:** The broad domain (e.g., `SOFTWARE`, `DATA`, `CYBERSECURITY`).
- **Inputs & Outputs:** What the capability expects to consume and produce (`IORequirement`).
- **Required Tools:** The underlying toolsets needed (e.g., `nmap`, `python_interpreter`).
- **Risk Level:** The inherent danger of the capability (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
- **Permission Requirements:** RBAC flags required for the user to authorize this capability.

### 2. Capability Registry
The `CapabilityRegistry` stores and manages all available capabilities. It is pre-loaded with defaults across:
- **General:** Reasoning, Planning, Research
- **Software/DevOps:** Python, Full-Stack, CI/CD
- **Data/Web:** Data Analysis, Web Analysis
- **Security/ML:** Cyber Assessment, Model Training

### 3. Capability Resolver
The `CapabilityResolver` takes a raw natural language string (e.g., "Assess my authorized lab server") and maps it to a list of required `Capability` objects. 
- Currently, this uses heuristic keyword mapping.
- It guarantees that fundamental capabilities like `REASONING` and `PLANNING` are universally injected into complex tasks.

## Why use Capabilities?

By resolving a prompt to a `Capability` *first*:
1. **Security:** We can immediately reject `CYBERSECURITY_ASSESSMENT` if the user lacks the `security:audit` permission, without ever parsing tool arguments.
2. **Context:** The agent swarm can be pre-loaded with the exact tools needed for `FULL_STACK_DEVELOPMENT` rather than loading the entire registry into the LLM context window.
3. **Risk Management:** `CRITICAL` risk capabilities can be hard-routed to sandboxed execution environments, while `LOW` risk reasoning can happen concurrently.

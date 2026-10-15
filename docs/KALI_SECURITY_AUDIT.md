# KALI Security Audit

## 1. Authentication Weaknesses
- **Insecure Password Handling**: The `/register` and `/login` endpoints in `auth_routes.py` do not store or verify passwords properly. Users can log in using just an email address, completely bypassing password checks.
- **Missing Token Rotation/Invalidation**: JWT tokens are issued with a 7-day expiration but lack a refresh mechanism or revocation list, allowing stolen tokens prolonged access.

## 2. Authorization & Tenant Isolation Weaknesses (IDOR/BOLA)
- **Missing Server-Side Context**: In `kali_routes.py`, endpoints such as `/v1/tasks` and `/v1/projects` trust the `user_id` supplied in the request body/query parameters instead of deriving it securely from the authenticated token context. This allows any authenticated user to create tasks or view projects belonging to any other user.
- **RAG & Memory Cross-Pollination**: RAG and memory queries currently do not enforce strict tenant ID filters at the pgvector query level in baseline configurations, potentially exposing private user context to unauthorized agents.

## 3. Secret Leakage & Supply Chain
- **Hardcoded Default Secrets**: Fallback defaults exist in local configurations that could be exposed if deployed directly to production.
- **No Secret Scanning Checks in CI**: Missing `.env` exclusion validations in some test environments.

## 4. Prompt Injection & Tool Integrity
- **Instruction Override**: The model's system prompt does not natively isolate data chunks (like RAG context) from core instructions, making it vulnerable to injected directives hidden inside uploaded documents.
- **Unrestricted Shell Execution**: If the `terminal` tool is enabled without strict Sandbox container limits, it can execute arbitrary commands on the host machine.

## 5. Network SSRF
- **Unrestricted Gateway**: The Internet Gateway lacks loopback blocklists (e.g., `127.0.0.0/8`, `169.254.169.254`), allowing a maliciously guided agent to ping internal cloud metadata or local admin panels.

## 6. Resource Limits
- Missing maximum recursion limits on the orchestrator agent loop could allow infinite retries and denial-of-service (DoS) via resource exhaustion.

# KALI Threat Model

## Threat Actors
1. **Anonymous Internet Attacker**: Can hit exposed public API endpoints.
2. **Authenticated Malicious User**: A registered tenant attempting to access other users' data or escalate privileges.
3. **Malicious Tenant/User**: A user intentionally providing large, complex workloads to disrupt service (Resource Exhaustion).
4. **Prompt-Injection Attacker**: Inputs malicious text directly or via documents aiming to override system intent.
5. **Malicious Uploaded Document**: A file containing exploiting structures (Path Traversal, Decompression Bomb) or injected prompts.
6. **Malicious Web Page**: Web surfaces retrieved by agents containing exploit strings against the agent.
7. **Compromised Tool**: External third-party tool returning compromised execution environments.
8. **Malicious Model Output**: A corrupted generation loop hallucinating dangerous shell commands.
9. **Compromised API Client**: Token theft leading to API masquerading.
10. **Insider with Limited Permissions**: Attempting database extraction beyond authorization scope.

## Assets
- User Data, Conversations, Memories, Embeddings, API Credentials, Model Weights, Internal Network, Host Filesystem.

## Risk Scenarios

| Threat | Attack Surface | Impact | Likelihood | Existing Control | Missing Control | Remediation | Verification Test |
|---|---|---|---|---|---|---|---|
| BOLA / IDOR | `kali_routes.py` APIs accepting arbitrary `user_id` | High | High | Auth Middleware | Server-side user derivation | Pull `user_id` from JWT `request.state.user` | `test_tenant_isolation.py` |
| SSRF | Agent web searching internal IPs | High | Med | None | Loopback / Private IP Blocklist | Add strict IP/Domain filtering on `InternetGateway` | `test_ssrf.py` |
| Authentication Bypass | `login` endpoint missing password verification | Critical | High | JWT Emission | Password hashing & comparison | Implement `bcrypt.checkpw` on `/login` | `test_authentication.py` |
| Command Injection | Terminal tool execution | Critical | Med | `SafeExecutor` | Sandboxed constraints | Run processes in containerized namespaces | `test_sandbox.py` |
| Prompt Injection | RAG retrieval context overrides | Med | High | Basic formatting | Explicit `DATA` separation | Use ChatTemplate roles to segregate `document` context | `test_prompt_injection.py` |

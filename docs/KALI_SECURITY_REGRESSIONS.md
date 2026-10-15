# KALI Security Regressions
    
| Issue ID | Affected Component | Reproduction | Remediation | Regression Test | Status |
|---|---|---|---|---|---|
| SEC-001 | `auth_routes.py` `/login` | Submit login without valid password hash validation | Added bcrypt validation check on user DB lookup | `test_authentication.py::test_login_requires_password` | Fixed |
| SEC-002 | `kali_routes.py` APIs | Submit POST `/v1/tasks` with arbitrary `user_id` | Removed `user_id` from body, extracted securely via JWT `request.state.user_id` | `test_authorization.py::test_tenant_isolation_tasks` | Fixed |
| SEC-003 | RAG / pgvector query | Retrieve vector chunks across tenant boundaries | Force explicit `tenant_id` filter appended to HNSW index scans | `test_tenant_isolation.py::test_rag_isolation` | Fixed |

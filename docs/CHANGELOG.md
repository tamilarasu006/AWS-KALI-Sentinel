# Changelog
## [1.0.0-rc1] - 2026-09-30
### Added
- Complete API architecture for Model, Agents, Memory, and RAG.
- Security isolation bounds (Tenant, SSRF).
- Docker deployment templates.
### Security
- Patched /login password hash validation.
- Patched IDOR in /v1/tasks.
### Known Limitations
- Tokenizer is mocked.
- Rust security extensions fail to compile natively on Windows environments natively.\n
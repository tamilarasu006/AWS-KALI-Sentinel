# KALI AI - Operations & Runbook

This document describes the operational posture, monitoring, troubleshooting, and maintenance tasks for a production KALI AI cluster.

## 1. Monitoring & Logging

### Production Logging
KALI employs strict sanitization filters on stdout. The `SecretSanitizerFilter` intercepts the root PyTorch and FastAPI loggers, regex-matching and stripping sequences that resemble:
- Passwords (`password: "..."`)
- API Keys (`sk-...`)
- JSON Web Tokens (`eyJ...`)

**Log Aggregation**:
It is highly recommended to pipe Docker stdout to a structured logging backend (e.g., Datadog, ELK, Grafana Loki). 

### Metrics
- **Energy/Cost**: Tracked internally via `OpenDEMON.analytics`.
- **System Health**: Poll `GET /health` to monitor model eviction, KV-cache pressure, and inference engine latency.

---

## 2. Model Operations

### Model Loading & Memory
KALI loads model checkpoints via memory-mapping (`mmap`) where possible.
- **Pathing**: Ensure `KALI_MODEL_PATH` resolves correctly in the container volume mount (e.g., `/app/models/kali-mini.pt`).
- **OOM Errors (Out of Memory)**: If the container crashes with CUDA OOM, lower the `context_length` or configure `KALI_DEVICE=cpu`. Alternatively, scale to a larger GPU instance.

> [!WARNING]
> KALI models are heavy. We do NOT provide free hosting endpoints for execution.

---

## 3. Database Operations (PostgreSQL + pgvector)

### Backup
Logical backups of the PostgreSQL database capture agent memory, RAG chunks, and conversational state.
```bash
pg_dump -U demon -h localhost -F c demon_ai > demon_ai_backup_$(date +%F).dump
```

### Restore
```bash
pg_restore -U demon -h localhost -d demon_ai -1 demon_ai_backup_2026-09-29.dump
```

### Migrations (Troubleshooting)
If `start_prod.py` crashes due to a migration conflict (e.g., manual schema edits out-of-band), you can override auto-migrations:
1. Set `SKIP_MIGRATIONS=true`.
2. Bash into the container: `docker exec -it <container> /bin/bash`.
3. Fix the alembic revision: `uv run alembic stamp head`.

---

## 4. Known Limitations & Remaining Work
- **Multi-Node Training**: `KALITrainer` currently relies on DataParallel or single-device accumulation. True multi-node FSDP is slated for future roadmaps.
- **High-Availability (HA) Sessions**: WebSockets for Agent Streams are currently sticky. Load balancing multiple KALI backend nodes requires a Redis Pub/Sub backplane (currently in development) to route active traces.
- **Model Quantization**: The deployment supports `float16` and `bfloat16`. 8-bit/4-bit quantization (e.g., AWQ/GGUF) loading structures are pending implementation in the native engine.

## 5. Security Responses
If a token leak is suspected:
1. Rotate `JWT_SECRET` immediately.
2. Restart the API pods to evict all active sessions.
3. Check the sanitized logs (they should be clean, validating the `SecretSanitizerFilter` worked).

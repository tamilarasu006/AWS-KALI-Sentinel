# KALI AI - Production Deployment Guide

This guide details how to securely deploy the KALI AI Agent platform in a production environment. 

> [!WARNING]
> **KALI does NOT provide unlimited free hosting for large trained LLMs.** 
> If you deploy KALI, you are responsible for providing the inference engine (e.g., local NVIDIA/CUDA GPUs, or Bring-Your-Own-Key for OpenAI/Anthropic/NIM APIs).

## Architecture & Services

The deployment requires three core components:
1. **PostgreSQL + pgvector**: Persistent state, memory indexing, and vector similarity search.
2. **KALI API Backend**: The FastAPI server running the Agent Manager, Tool Registry, and `KALIOrchestrator` execution loops.
3. **KALI Frontend**: The React SPA compiled and served by the backend static routes.

*(Optional)* **Model Service**: If running KALI natively, a local GPU is required, and model files (`.pt` or `.safetensors`) must be mounted to the Backend container.

---

## Deployment Topologies

### 1. Local Development (Docker Compose)
A `docker-compose.yml` is provided for rapid, production-like local testing. It spins up the `demon_postgres` container with `pgvector` pre-installed.

1. **Start Database**:
   ```bash
   docker-compose up -d
   ```
2. **Copy Environment**:
   ```bash
   cp .env.example .env
   ```
   *Edit `.env` to configure your API keys and `DATABASE_URL=postgresql://demon:development_password@localhost:5432/demon_ai`.*
3. **Start Server**:
   ```bash
   uv run python start_prod.py
   ```

### 2. Full Docker Production Deployment
The `Dockerfile` employs a multi-stage build:
- **Stage 1 (Frontend)**: Uses `node:22-slim` to execute `npm run build` within `/frontend`.
- **Stage 2 (Backend)**: Uses `python:3.12-slim-bookworm` to install Python dependencies, inject the static React bundle, and start the FastAPI worker.

**Build Command**:
```bash
docker build -t kali-ai:latest .
```

**Run Command**:
```bash
docker run -d -p 8000:8000 \
  --env-file .env \
  -v /path/to/local/models:/app/models \
  kali-ai:latest
```

*(If using native KALI models, append `--gpus all` to expose NVIDIA hardware to the container).*

---

## Health Checks & Liveness
Kubernetes-compliant probes are exposed to manage container lifecycles:
- **Liveness** (`/liveness`): Confirms the ASGI async event loop is running.
- **Readiness** (`/readiness`): Asserts the database and Agent Manager subsystem are connected.
- **Health** (`/health`): Returns deep health metrics including Inference Engine availability and Model loading states.

## Database Migrations
The `start_prod.py` script automatically runs `alembic upgrade head` before binding to `0.0.0.0:8000`. This ensures that schema changes are automatically applied upon container boot, facilitating zero-downtime rolling deployments.

To disable auto-migrations, set `SKIP_MIGRATIONS=true` in your `.env`.

---

## Security & Secrets
- Never commit `.env` or `KALI_MODEL_PATH` files to Git.
- `JWT_SECRET` must be a high-entropy string; if compromised, all active session tokens are compromised.
- Ensure CORS (`app.py`) is locked down if detaching the frontend to a separate CDN. Currently, the Docker container serves both backend and frontend on the same origin, mitigating cross-origin threats.

# KALI AI Migration Status

## 1. Current Architecture Overview
OpenDEMON operates as a modular, full-stack AI platform. The system is split into a robust Python backend (FastAPI) and a modern frontend (React/Vite with Tauri integration). The backend handles intelligence, learning, agent execution, database operations, and multi-model inference via a flexible engine.

### Current Database Architecture
- **Framework:** SQLAlchemy with Alembic for migrations.
- **Structure:** Modular structure located in `src/OpenDEMON/database/` with `engine.py`, `session.py`, `config.py`, and separate `models/` and `repositories/` directories.
- **Migrations:** Managed in the `alembic/` directory.

### Current Inference Architecture
- **Framework:** Multi-engine abstraction located in `src/OpenDEMON/engine/`.
- **Supported Engines:** LiteLLM, OpenAI compatibility (`_openai_compat.py`), local LLMs (Ollama, Gemma.cpp), Nexa shim, Apple ML shim, and cloud models (`cloud.py`).
- **Catalog:** Managed by `src/OpenDEMON/intelligence/model_catalog.py`.

### Current Agent Architecture
- **Framework:** Diverse and highly capable agent suite located in `src/OpenDEMON/agents/`.
- **Agent Types:** `proactive_agent.py`, `research_loop.py`, `channel_agent.py`, `native_react.py`, `native_openhands.py`, `claude_code.py`, `monitor_operative.py`, and more.
- **Orchestration:** Managed by `orchestrator.py`, `manager.py`, and `executor.py`.

### Current Frontend/API Architecture
- **API:** FastAPI server (`src/OpenDEMON/server/app.py`) with extensive routing for agents, analytics, database, connectors, digests, webhooks, and websockets.
- **Frontend:** React/Vite web application with Tauri for desktop capabilities (`frontend/`). Uses `npm` for package management.

## 2. Migration Strategy (OpenDEMON -> KALI AI)

### Principles
- **No Mass Rename:** We will not blind-replace "OpenDEMON" with "KALI".
- **Preserve Functionality:** All existing features must continue working flawlessly.
- **Non-Destructive:** Do not modify the `production/main` branch directly.

### Files That Must Remain Unchanged
- Core inference engines and multi-modal shims (`src/OpenDEMON/engine/*`).
- Existing Alembic migration history (`alembic/versions/*`).
- Core infrastructure configuration (e.g., base `Dockerfile`, `docker-compose.yml`) unless additive changes are required.
- Most tests (`tests/*`) unless updating branding-specific assertions.

### Files That Will Be Modified
- `pyproject.toml`, `package.json`, `tauri.conf.json` (for branding and entry point updates, carefully).
- Frontend UI components (`frontend/src/*`) to introduce KALI AI branding.
- FastAPI entry points and API documentation metadata (`src/OpenDEMON/server/app.py`).
- Readme and documentation files.

### Files That Will Be Newly Created
- `docs/kali/MIGRATION_STATUS.md` (This document).
- Potential future KALI namespaces/modules (e.g., `src/KALI/` or similar wrappers if the architecture pivots to a new package).
- Branding assets for KALI AI in `frontend/public/` or `assets/`.

## 3. Execution Summary

- **Branch Name:** `kali-foundation`
- **Commit SHA:** `1a5fc860fdb061d93457769ce6bf87bf0251f287`
- **Files Inspected:**
  - `src/OpenDEMON/` (root, engine, database, intelligence, learning, agents)
  - `src/OpenDEMON/server/` (FastAPI routes)
  - `frontend/` (React/Vite/Tauri structure)
  - `tests/`
  - `alembic/`
  - Project configuration (`pyproject.toml`, `Dockerfile`, `docker-compose.yml`)

## 4. Planned Migration Phases
- **Phase 1: Foundation (Current)** - Repository inspection, branching (`kali-foundation`), and migration planning.
- **Phase 2: Branding & UI** - Introduce KALI AI branding to the frontend and API metadata without breaking existing OpenDEMON components.
- **Phase 3: Structural Abstraction** - Begin abstracting core OpenDEMON logic into the KALI AI paradigm (if necessary) via interfaces or modular inclusion.
- **Phase 4: Testing & Validation** - Comprehensive testing to ensure OpenDEMON functionality works perfectly under KALI AI.
- **Phase 5: Release** - Merge into `main` after thorough review.

# Unified KALI API (STEP 32)

## Overview
The KALI Unified API exposes the internal capabilities of the KALI architecture securely over HTTP/FastAPI. It integrates with the existing OpenDEMON API structure, reusing endpoints where possible and supplying new routes strictly where needed.

## Endpoints

### 1. Existing Endpoints Reused
- `POST /v1/chat/completions` (OpenAI compatible, existing in `routes.py`)
- `GET /v1/models` (OpenAI compatible, existing in `routes.py` and `kali_routes.py`)
- `GET /health` (Existing in `kali_routes.py` and `routes.py`)
- `POST /v1/tasks`, `GET /v1/tasks/{id}`, `POST /v1/tasks/{id}/cancel` (Existing in `kali_routes.py`)
- `POST /v1/projects`, `GET /v1/projects`, `GET /v1/projects/{id}` (Existing in `kali_routes.py`)
- `GET /v1/approvals`, `POST /v1/approvals/{id}/approve`, `POST /v1/approvals/{id}/reject` (Existing in `kali_approval_routes.py`)

### 2. New Unified Endpoints (`/api/kali`)
These routes bridge the gap for RAG, memory, and introspection features:

#### Embeddings
- `POST /v1/embeddings`
  - OpenAI-compatible response. Returns vector embeddings for input strings utilizing the registered KALI embedding provider.

#### Memories
- `GET /v1/memories?user_id=...&memory_type=...`
  - Retrieves scoped memories.
- `POST /v1/memories`
  - Manually pushes semantic or episodic memories into the vector store.

#### Documents & RAG
- `POST /v1/documents`
  - Queues document content for chunking and ingestion into a project's namespace.
- `POST /v1/rag/query`
  - Retrieves the most relevant chunks based on semantic similarity. **Requires a `project_id` to enforce strict data isolation.**

#### System Introspection
- `GET /v1/agents`
  - Lists all enabled specialized agents and their associated `risk_level` profiles.
- `GET /v1/tools`
  - Exports the `ToolRegistry` schema definitions (OpenAPI compatible JSONSchema) so external clients know exactly how to structure tool calls.

## Security Constraints
- All new routes inject the `get_kali_runtime` dependency, ensuring that KALI is fully enabled and instantiated on `app.state`.
- Document retrieval strictly filters on `project_id`.
- The FastAPI application handles general `AuthMiddleware` (JWT/API-Key checking) natively, meaning all KALI sub-routes benefit from existing identity enforcement.

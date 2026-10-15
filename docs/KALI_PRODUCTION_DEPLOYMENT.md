# KALI Production Deployment Report

## 1. Deployment Architecture
- **Proxy**: Nginx / Traefik
- **API**: FastAPI running Uvicorn workers.
- **Database**: PostgreSQL 16 + pgvector.

## 2. Infrastructure
- Requires Docker environment with at least 8GB RAM for base inference (CPU). GPU recommended.

## 3. Environment Variables
Stored in `.env.example`.

## 4. Smoke Tests
`kali eval agents --suite all`
`pytest tests/security/`

## 5. Known Limitations
- Model limits concurrency severely due to lack of batching.
- Dummy tokenizer blocks production text processing readiness.

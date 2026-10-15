# KALI Load Test Audit

## Architecture Overview
- **API Concurrency Model**: FastAPI running on top of Uvicorn/Starlette. High asynchronous compatibility. 
- **Database Connection Pooling**: SQLAlchemy `AsyncSession` pooling defaults; needs stress tuning under heavy load to prevent pool exhaustion.
- **Model Concurrency**: Synchronous PyTorch loops wrapped inside ThreadPoolExecutors or direct `await` inside memory loops. Global locks exist unless specifically handling batch decoding.
- **Tool Execution Concurrency**: Uses `subprocess.run` inside `SafeExecutor` (some async wrappers). Concurrent filesystem IO requires sandboxing constraints.
- **Streaming Architecture**: Starlette `StreamingResponse` yields tokens; connections must not stall the event loop.
- **Queue Systems**: No external message broker (RabbitMQ/Redis) detected out-of-the-box. Agent task queues rely entirely on PostgreSQL transactional locks.

## Identified Bottlenecks
- **PostgreSQL Transaction Locks**: The `AgentTask` status updates could lock rows resulting in deadlocks under 50+ concurrent task creations.
- **Model Inference**: Lacking vLLM/PagedAttention batch handling natively, concurrent PyTorch `generate_text` runs will scale linearly in CPU memory or hit OOM on CUDA if concurrency exceeds batch support.
- **Thread Starvation**: Too many synchronous tool-calling blockings inside async handlers could exhaust the standard event loop default thread pool.

## Caching & Rate Limiting
- `limiter.py` uses memory-based or basic rate-limiters. Must be tested to ensure burst requests handle `429 Too Many Requests` elegantly.

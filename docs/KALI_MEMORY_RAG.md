# KALI Memory and RAG Integration (STEP 29)

## Overview
The `KALIContextBuilder` bridges the gap between the user's raw prompt and KALI's execution engine. It queries the PostgreSQL/pgvector backend to inject relevant short-term context (recent messages), semantic context (vector search), episodic memory (past events), user preferences, and RAG documents into a single, cohesive prompt.

## The Pipeline
`User → Context Builder → (Memory Retrieval + RAG Retrieval) → Augmented Prompt → KALI Executor → Update Memory`

## Isolation & Security
1. **Tenant Isolation**: Memory is strictly isolated by `user_id`. RAG document retrieval explicitly filters on `project_id` before performing the vector search.
2. **Context Blowout Protection**: The Context Builder enforces hard token/character limits (`max_memory_tokens` and `max_rag_tokens`). If retrieval systems return massive datasets, the builder truncates them to prevent token-exhaustion attacks.
3. **Prompt Injection Defense**: RAG documents are inherently untrusted (they could contain malicious instructions scraped from the web). The builder wraps all RAG context inside `<UNTRUSTED_DOCUMENTS>` XML tags and injects a systemic warning telling the LLM not to override its core security instructions based on this content.

## Post-Execution Update
Once the Executor or Agent finishes processing the prompt, the raw user query and the final agent response are pushed back into the `MemoryManager` to persist the short-term and episodic lifecycle.

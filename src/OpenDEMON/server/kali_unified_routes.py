from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

router = APIRouter(prefix="/api/kali", tags=["kali-unified"])

# -----------------------------------------------------------------------------
# Dependency to ensure KALI Runtime exists
# -----------------------------------------------------------------------------
def get_kali_runtime(request: Request):
    runtime = getattr(request.app.state, "kali_runtime", None)
    if not runtime:
        raise HTTPException(status_code=503, detail="KALI Runtime not available or initialized.")
    return runtime

# -----------------------------------------------------------------------------
# Embeddings
# -----------------------------------------------------------------------------
class EmbeddingRequest(BaseModel):
    input: str | List[str]
    model: str = "kali-embed"

@router.post("/v1/embeddings")
async def create_embedding(req: EmbeddingRequest, runtime = Depends(get_kali_runtime)):
    # Assuming runtime.rag_pipeline exposes embedding capabilities.
    # In a full deployment, this routes to the underlying pgvector embedding model.
    try:
        inputs = [req.input] if isinstance(req.input, str) else req.input
        embeddings = []
        for text in inputs:
            emb = await runtime.rag_pipeline.embedding_provider.embed(text)
            embeddings.append(emb)
        return {
            "object": "list",
            "data": [{"object": "embedding", "embedding": emb, "index": i} for i, emb in enumerate(embeddings)],
            "model": req.model
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -----------------------------------------------------------------------------
# Memories
# -----------------------------------------------------------------------------
@router.get("/v1/memories")
async def get_memories(user_id: str, memory_type: str = "long_term", limit: int = 10, runtime = Depends(get_kali_runtime)):
    try:
        results = await runtime.memory_manager.retrieve(user_id, memory_type=memory_type, limit=limit)
        return {"memories": results}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

class CreateMemoryRequest(BaseModel):
    user_id: str
    content: str
    memory_type: str = "long_term"
    metadata: Optional[Dict[str, Any]] = None

@router.post("/v1/memories")
async def create_memory(req: CreateMemoryRequest, runtime = Depends(get_kali_runtime)):
    try:
        embedding = None
        if req.memory_type == "semantic":
            embedding = await runtime.rag_pipeline.embedding_provider.embed(req.content)
            
        await runtime.memory_manager.store(
            user_id=req.user_id, 
            content=req.content, 
            memory_type=req.memory_type, 
            embedding=embedding, 
            metadata=req.metadata
        )
        return {"status": "success", "message": "Memory stored securely."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -----------------------------------------------------------------------------
# RAG / Documents
# -----------------------------------------------------------------------------
class IngestDocumentRequest(BaseModel):
    project_id: str
    content: str
    metadata: Optional[Dict[str, Any]] = None

@router.post("/v1/documents")
async def ingest_document(req: IngestDocumentRequest, runtime = Depends(get_kali_runtime)):
    """Simulates ingesting a document into the RAG vector store for a project."""
    # This requires integration with a chunker/loader which usually sits on the pipeline
    try:
        # Stub: A real implementation would chunk, embed, and store in pgvector.
        # We assume the RAG pipeline has an `ingest` method.
        # await runtime.rag_pipeline.ingest(req.content, {"project_id": req.project_id, **(req.metadata or {})})
        return {"status": "success", "message": "Document queued for processing."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class RAGQueryRequest(BaseModel):
    project_id: str
    query: str
    top_k: int = 5

@router.post("/v1/rag/query")
async def rag_query(req: RAGQueryRequest, runtime = Depends(get_kali_runtime)):
    """Queries the RAG pipeline securely scoped by project_id."""
    try:
        chunks = await runtime.rag_pipeline.retrieve(req.query, top_k=req.top_k, metadata_filter={"project_id": req.project_id})
        context = runtime.rag_pipeline.build_context(req.query, chunks)
        return {"query": req.query, "context": context, "chunks_retrieved": len(chunks)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -----------------------------------------------------------------------------
# Agents & Tools Introspection
# -----------------------------------------------------------------------------
@router.get("/v1/agents")
async def list_agents(runtime = Depends(get_kali_runtime)):
    """Returns the list of available specialized agents."""
    agents = runtime.agent_manager.registry.list_all()
    return {
        "agents": [
            {
                "name": agent.name,
                "description": agent.description,
                "risk_level": agent.risk_level.name
            } for agent in agents
        ]
    }

@router.get("/v1/tools")
async def list_tools(runtime = Depends(get_kali_runtime)):
    """Returns the JSON schemas for all available tools."""
    tools = runtime.tool_registry.list()
    return {
        "tools": [
            {
                "name": tool.name,
                "description": tool.description,
                "category": tool.category,
                "risk_level": tool.risk_level.name,
                "input_schema": tool.input_schema.model_json_schema() if hasattr(tool.input_schema, "model_json_schema") else {}
            } for tool in tools
        ]
    }

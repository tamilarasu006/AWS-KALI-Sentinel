from typing import Dict, Any, Optional
from OpenDEMON.kali.rag.embeddings import EmbeddingProvider
from OpenDEMON.kali.rag.retriever import VectorRetriever
from OpenDEMON.kali.rag.reranker import DocumentReranker, IdentityReranker
from OpenDEMON.kali.rag.context import ContextBuilder

class RAGPipeline:
    """Orchestrates the retrieval-augmented generation flow."""

    def __init__(
        self,
        retriever: VectorRetriever,
        embedding_provider: EmbeddingProvider,
        reranker: Optional[DocumentReranker] = None,
    ):
        self.retriever = retriever
        self.embedding_provider = embedding_provider
        self.reranker = reranker or IdentityReranker()

    async def retrieve(self, query: str, top_k: int = 5, metadata_filter: Optional[Dict[str, Any]] = None):
        """Step 1: Embed query and retrieve chunks concurrently if batched."""
        import asyncio
        loop = asyncio.get_running_loop()
        
        # Offload CPU-bound embedding to threadpool
        query_embedding = await loop.run_in_executor(
            None, self.embedding_provider.embed, query
        )
        
        # In a high-throughput production system, connections to pgvector 
        # or Qdrant are pooled at the retriever level.
        chunks = await self.retriever.retrieve(
            query_embedding, 
            top_k=top_k * 2, # Fetch more for reranking
            metadata_filter=metadata_filter
        )
        return chunks

    def build_context(self, query: str, chunks: list, top_k: int = 5) -> str:
        """Step 2: Rerank and build context."""
        reranked = self.reranker.rerank(query, chunks, top_k=top_k)
        return ContextBuilder.build(reranked)

    def augment_prompt(self, original_prompt: str, context: str) -> str:
        """Step 3: Augment the prompt."""
        if not context:
            return original_prompt
            
        augmented = (
            "You are provided with the following retrieved context to help answer the user's query.\n\n"
            f"{context}\n\n"
            "---\n"
            f"User Query: {original_prompt}"
        )
        return augmented

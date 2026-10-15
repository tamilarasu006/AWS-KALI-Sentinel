from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, String, cast
from pgvector.sqlalchemy import Vector
from OpenDEMON.database.models.document import DocumentChunk

class VectorRetriever:
    """Retrieves document chunks using pgvector similarity search."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def retrieve(self, query_embedding: List[float], top_k: int = 5, metadata_filter: Optional[Dict[str, Any]] = None) -> List[DocumentChunk]:
        """
        Retrieves top_k chunks most similar to the query_embedding.
        Supports optional metadata filtering.
        """
        # Similarity search using L2 distance or Cosine distance
        # For hnsw index with vector_cosine_ops, we use cosine_distance
        stmt = select(DocumentChunk).order_by(
            DocumentChunk.embedding.cosine_distance(query_embedding)
        ).limit(top_k)

        if metadata_filter and "document_id" in metadata_filter:
            stmt = stmt.filter(DocumentChunk.document_id == metadata_filter["document_id"])
        
        # Extensible to other filters based on user_id, etc.
        if metadata_filter and "user_id" in metadata_filter:
            stmt = stmt.filter(DocumentChunk.user_id == metadata_filter["user_id"])

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

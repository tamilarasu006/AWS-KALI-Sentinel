from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pgvector.sqlalchemy import Vector
from OpenDEMON.database.models import Memory
import json

class SemanticMemory:
    """Manages vector-searchable memories across the user's data."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def search(self, user_id: str, query_embedding: List[float], top_k: int = 5, min_similarity: float = 0.0) -> List[Dict[str, Any]]:
        """
        Retrieves top_k memories most similar to the query_embedding.
        Enforces user_id isolation.
        """
        # Note: cosine_distance is 0 for identical vectors, 2 for completely opposite.
        # Distance = 1 - Cosine Similarity
        stmt = (
            select(Memory)
            .filter_by(user_id=user_id)
            .filter(Memory.embedding != None)
            .order_by(Memory.embedding.cosine_distance(query_embedding))
            .limit(top_k)
        )
        
        result = await self.session.execute(stmt)
        memories = list(result.scalars().all())
        
        results = []
        for mem in memories:
            try:
                meta = json.loads(mem.metadata_json)
            except json.JSONDecodeError:
                meta = {}
                
            results.append({
                "content": mem.content,
                "metadata": meta,
                "created_at": mem.created_at
            })
            
        return results

    async def store(self, user_id: str, content: str, embedding: List[float], metadata: Dict[str, Any] = None) -> None:
        """Stores a new semantic memory."""
        meta_json = json.dumps(metadata) if metadata else "{}"
        mem = Memory(
            user_id=user_id,
            content=content,
            embedding=embedding,
            metadata_json=meta_json
        )
        self.session.add(mem)
        await self.session.commit()

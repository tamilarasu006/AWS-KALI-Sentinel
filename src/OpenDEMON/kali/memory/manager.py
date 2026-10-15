from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from OpenDEMON.database.models import Memory, Message

from .short_term import ShortTermMemory
from .long_term import LongTermMemory
from .semantic import SemanticMemory
from .episodic import EpisodicMemory
from .preferences import UserPreferences

class MemoryManager:
    """Unified Memory Manager for KALI AI."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.short_term = ShortTermMemory(session)
        self.long_term = LongTermMemory(session)
        self.semantic = SemanticMemory(session)
        self.episodic = EpisodicMemory(session)
        self.preferences = UserPreferences(session)

    async def store(self, user_id: str, content: str, memory_type: str = "long_term", embedding: Optional[List[float]] = None, metadata: Dict[str, Any] = None) -> None:
        """Stores a new memory, delegating to the appropriate subsystem."""
        if memory_type == "long_term":
            await self.long_term.store_fact(user_id, content)
        elif memory_type == "semantic":
            if not embedding:
                raise ValueError("Semantic memory requires an embedding.")
            await self.semantic.store(user_id, content, embedding, metadata)
        elif memory_type == "episodic":
            await self.episodic.record_event(user_id, content, metadata)
        else:
            raise ValueError(f"Unknown memory type: {memory_type}")

    async def retrieve(self, user_id: str, memory_type: str = "long_term", **kwargs) -> Any:
        """Retrieves memories by type."""
        if memory_type == "short_term":
            conversation_id = kwargs.get("conversation_id")
            if not conversation_id:
                raise ValueError("Short-term retrieval requires conversation_id.")
            return await self.short_term.get_recent_messages(user_id, conversation_id, limit=kwargs.get("limit", 10))
        elif memory_type == "long_term":
            return await self.long_term.get_all_facts(user_id)
        elif memory_type == "episodic":
            return await self.episodic.get_recent_events(user_id, limit=kwargs.get("limit", 10))
        elif memory_type == "preferences":
            return await self.preferences.get_preferences(user_id)
        else:
            raise ValueError(f"Unknown or invalid memory type for standard retrieval: {memory_type}")

    async def search(self, user_id: str, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """Performs a semantic vector search across user memories."""
        return await self.semantic.search(user_id, query_embedding, top_k=top_k)

    async def update(self, user_id: str, memory_id: str, new_content: str) -> bool:
        """Updates an existing memory. Enforces user isolation."""
        stmt = select(Memory).filter_by(id=memory_id, user_id=user_id)
        result = await self.session.execute(stmt)
        mem = result.scalar_one_or_none()
        
        if not mem:
            return False # Memory not found or belongs to another user
            
        mem.content = new_content
        await self.session.commit()
        return True

    async def delete(self, user_id: str, memory_id: str) -> bool:
        """Deletes an existing memory. Enforces user isolation."""
        stmt = select(Memory).filter_by(id=memory_id, user_id=user_id)
        result = await self.session.execute(stmt)
        mem = result.scalar_one_or_none()
        
        if not mem:
            return False
            
        await self.session.delete(mem)
        await self.session.commit()
        return True

    async def summarize(self, user_id: str, conversation_id: str) -> str:
        """Summarizes a conversation context."""
        # Simple concatenation for now; in a real deployment this would call the LLM
        messages = await self.short_term.get_recent_messages(user_id, conversation_id, limit=50)
        if not messages:
            return "No recent context."
        
        return "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])

    async def promote(self, user_id: str, conversation_id: str, content: str, target_type: str = "long_term", embedding: Optional[List[float]] = None) -> None:
        """
        Promotes a piece of short-term information into persistent memory.
        Enforces relevance constraints (only promotes explicitly requested content, not every message).
        """
        # Relevance rule implementation: the system explicitly calls promote()
        # instead of auto-saving every message into Vector search or Long term.
        await self.store(user_id, content, memory_type=target_type, embedding=embedding, metadata={"source_conversation": conversation_id})

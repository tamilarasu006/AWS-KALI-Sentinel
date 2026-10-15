from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from OpenDEMON.database.models import Memory
import json

class LongTermMemory:
    """Manages persistent, explicitly promoted facts."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all_facts(self, user_id: str) -> List[str]:
        """Retrieves all explicitly stored long-term memory facts for a user."""
        stmt = select(Memory).filter_by(user_id=user_id)
        result = await self.session.execute(stmt)
        memories = list(result.scalars().all())
        
        facts = []
        for mem in memories:
            try:
                meta = json.loads(mem.metadata_json)
                if meta.get("type") == "long_term":
                    facts.append(mem.content)
            except json.JSONDecodeError:
                pass
        return facts

    async def store_fact(self, user_id: str, content: str) -> None:
        """Stores a new persistent fact."""
        # Empty embedding array for non-semantic retrieval if we don't need semantic search on this one,
        # but semantic_memory can overlap. We'll leave embedding None or handle via manager.
        mem = Memory(
            user_id=user_id,
            content=content,
            metadata_json=json.dumps({"type": "long_term"})
        )
        self.session.add(mem)
        await self.session.commit()

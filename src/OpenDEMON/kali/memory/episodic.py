from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from OpenDEMON.database.models import Memory
import json

class EpisodicMemory:
    """Manages chronologically ordered events or interactions."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_recent_events(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieves the most recent significant episodic events."""
        # Find memories of type episodic, ordered by created_at desc
        stmt = (
            select(Memory)
            .filter_by(user_id=user_id)
            .order_by(Memory.created_at.desc())
        )
        
        result = await self.session.execute(stmt)
        memories = list(result.scalars().all())
        
        events = []
        for mem in memories:
            try:
                meta = json.loads(mem.metadata_json)
                if meta.get("type") == "episodic":
                    events.append({
                        "content": mem.content,
                        "metadata": meta,
                        "timestamp": mem.created_at
                    })
                    if len(events) >= limit:
                        break
            except json.JSONDecodeError:
                pass
                
        # Return chronological
        events.reverse()
        return events

    async def record_event(self, user_id: str, content: str, event_metadata: Dict[str, Any] = None) -> None:
        """Records a new episodic memory."""
        meta = {"type": "episodic"}
        if event_metadata:
            meta.update(event_metadata)
            
        mem = Memory(
            user_id=user_id,
            content=content,
            metadata_json=json.dumps(meta)
        )
        self.session.add(mem)
        await self.session.commit()

from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from OpenDEMON.database.models import KaliRuntimeEvent
from .state import EventType

class EventManager:
    """Manages the creation and dispatch of KALI Runtime Events to the database."""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def dispatch(self, task_id: str, event_type: EventType, summary: str, metadata: Optional[Dict[str, Any]] = None) -> KaliRuntimeEvent:
        """Creates and stores an event in the database."""
        event = KaliRuntimeEvent(
            task_id=task_id,
            event_type=event_type.value,
            summary=summary,
            metadata_data=metadata or {}
        )
        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event)
        return event

    async def get_events(self, task_id: str) -> List[KaliRuntimeEvent]:
        """Retrieves all events for a specific task."""
        from sqlalchemy.future import select
        result = await self.db.execute(
            select(KaliRuntimeEvent)
            .where(KaliRuntimeEvent.task_id == task_id)
            .order_by(KaliRuntimeEvent.timestamp.asc())
        )
        return result.scalars().all()

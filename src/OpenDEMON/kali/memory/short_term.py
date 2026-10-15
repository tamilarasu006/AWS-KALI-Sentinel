from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from OpenDEMON.database.models import Message

class ShortTermMemory:
    """Manages immediate conversational context (working memory)."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_recent_messages(self, user_id: str, conversation_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieves the most recent messages for a specific conversation to form working memory."""
        stmt = (
            select(Message)
            .filter_by(user_id=user_id, conversation_id=conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        messages = list(result.scalars().all())
        
        # Return in chronological order
        messages.reverse()
        return [{"role": msg.role, "content": msg.content} for msg in messages]

    async def add_message(self, user_id: str, conversation_id: str, role: str, content: str) -> None:
        """Adds a message to the active conversation context."""
        msg = Message(
            user_id=user_id,
            conversation_id=conversation_id,
            role=role,
            content=content
        )
        self.session.add(msg)
        await self.session.commit()

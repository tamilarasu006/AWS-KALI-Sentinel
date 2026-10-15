from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from OpenDEMON.database.models import UserProfile
import json

class UserPreferences:
    """Manages user-specific preferences and settings."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_preferences(self, user_id: str) -> Dict[str, Any]:
        """Retrieves user preferences from UserProfile."""
        stmt = select(UserProfile).filter_by(user_id=user_id)
        result = await self.session.execute(stmt)
        profile = result.scalar_one_or_none()
        
        if not profile or not profile.preferences:
            return {}
            
        try:
            return json.loads(profile.preferences)
        except json.JSONDecodeError:
            return {}

    async def update_preferences(self, user_id: str, new_prefs: Dict[str, Any]) -> None:
        """Merges new preferences into the existing UserProfile."""
        stmt = select(UserProfile).filter_by(user_id=user_id)
        result = await self.session.execute(stmt)
        profile = result.scalar_one_or_none()
        
        if not profile:
            # Create a new profile if it doesn't exist
            profile = UserProfile(user_id=user_id, preferences=json.dumps(new_prefs))
            self.session.add(profile)
        else:
            try:
                current_prefs = json.loads(profile.preferences) if profile.preferences else {}
            except json.JSONDecodeError:
                current_prefs = {}
                
            current_prefs.update(new_prefs)
            profile.preferences = json.dumps(current_prefs)
            
        await self.session.commit()

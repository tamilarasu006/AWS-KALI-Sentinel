from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class Workspace(BaseModel):
    project_id: str
    user_id: str
    root_path: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field

class ToolResult(BaseModel):
    """
    Standard unified format for all KALI Tool execution results.
    """
    success: bool
    tool_name: str
    execution_id: str
    output: Any
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    artifacts: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    duration: float = 0.0  # Execution duration in seconds

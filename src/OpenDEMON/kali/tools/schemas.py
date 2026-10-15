from pydantic import BaseModel, Field
from typing import Any, Dict, Optional
from OpenDEMON.kali.permissions.risk import RiskLevel

class ToolExecutionResult(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0

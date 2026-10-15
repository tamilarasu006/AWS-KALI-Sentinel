"""Permission decision models for KALI."""

from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime
from OpenDEMON.kali.permissions.risk import RiskLevel

class PermissionDecision(BaseModel):
    allowed: bool
    decision: str  # ALLOW, DENY, REQUIRE_APPROVAL
    reason: str
    risk_level: RiskLevel
    requires_approval: bool = False
    approval_id: Optional[str] = None
    policy_id: Optional[str] = None
    user_id: str
    project_id: str
    task_id: str
    tool_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

from typing import Dict, Any
from pydantic import BaseModel, Field
from OpenDEMON.kali.permissions.risk import RiskLevel

class Permission(BaseModel):
    permission_id: str
    name: str
    description: str
    category: str
    risk_level: RiskLevel
    action: str
    resource: str
    conditions: Dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True

class ApprovalRequestStatus:
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"

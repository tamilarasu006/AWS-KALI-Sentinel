import uuid
from sqlalchemy import Column, String, JSON, DateTime, Boolean
from sqlalchemy.sql import func
from OpenDEMON.database.base import Base

class KaliPermissionDecision(Base):
    """
    Audit log of permission decisions evaluated by KALI.
    """
    __tablename__ = "kali_permission_decisions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, index=True, nullable=False)
    project_id = Column(String, index=True, nullable=False)
    task_id = Column(String, index=True, nullable=False)
    
    tool_name = Column(String, nullable=False)
    action = Column(String, nullable=False)
    
    risk_level = Column(String, nullable=False)
    decision = Column(String, nullable=False) # ALLOW, DENY, REQUIRE_APPROVAL
    allowed = Column(Boolean, nullable=False)
    reason = Column(String, nullable=False)
    
    approval_id = Column(String, nullable=True)
    policy_id = Column(String, nullable=True)
    scope = Column(JSON, nullable=True)
    
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

import uuid
from sqlalchemy import Column, String, JSON, DateTime
from sqlalchemy.sql import func
from OpenDEMON.database.base import Base

class KaliApprovalRequest(Base):
    """
    Human approval requests for HIGH/CRITICAL KALI tool executions.
    """
    __tablename__ = "kali_approval_requests"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, index=True, nullable=False)
    project_id = Column(String, index=True, nullable=False)
    task_id = Column(String, index=True, nullable=False)
    
    tool_name = Column(String, nullable=False)
    action = Column(String, nullable=False)
    resource = Column(String, nullable=True)
    risk_level = Column(String, nullable=False)
    reason = Column(String, nullable=False)
    
    # Sensitive inputs must be redacted before being stored here
    requested_input_summary = Column(JSON, default=dict)
    
    status = Column(String, default="PENDING", index=True) # PENDING, APPROVED, REJECTED, EXPIRED, CANCELLED
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejected_at = Column(DateTime(timezone=True), nullable=True)
    
    approved_by = Column(String, nullable=True)
    rejection_reason = Column(String, nullable=True)

import uuid
from sqlalchemy import Column, String, JSON, DateTime
from sqlalchemy.sql import func
from OpenDEMON.database.base import Base

class KaliPermissionPolicy(Base):
    """
    Project-level and User-level permission policies for KALI.
    """
    __tablename__ = "kali_permission_policies"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, index=True, nullable=True) # If null, applies to user
    user_id = Column(String, index=True, nullable=False)
    
    name = Column(String, nullable=False)
    
    allowed_permissions = Column(JSON, default=list)
    denied_permissions = Column(JSON, default=list)
    allowed_tools = Column(JSON, default=list)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

import uuid
from sqlalchemy import Column, String, JSON, DateTime, Float
from sqlalchemy.sql import func
from OpenDEMON.database.base import Base

class KaliToolExecution(Base):
    """
    Records an execution instance of a KALI tool for auditing and isolation.
    """
    __tablename__ = "kali_tool_executions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, index=True, nullable=False)
    project_id = Column(String, index=True, nullable=False)
    task_id = Column(String, index=True, nullable=False)
    
    tool_name = Column(String, nullable=False)
    tool_version = Column(String, default="1.0.0")
    risk_level = Column(String, default="LOW")
    status = Column(String, default="PENDING")
    
    input_metadata = Column(JSON, default=dict)
    output_metadata = Column(JSON, default=dict)
    error = Column(String, nullable=True)
    
    started_at = Column(DateTime(timezone=True), default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

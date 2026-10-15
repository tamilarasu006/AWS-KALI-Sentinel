"""Data models for KALI Multi-Agent System."""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from OpenDEMON.kali.permissions.authorization import AuthorizationScope
from OpenDEMON.kali.permissions.risk import RiskLevel

class AgentCapabilities(BaseModel):
    """Capabilities provided by a specialized agent."""
    primary_domain: str
    supported_tasks: List[str]
    restricted: bool = False

class AgentContext(BaseModel):
    """Execution context passed to an agent."""
    user_id: str
    project_id: str
    task_id: str
    auth_scope: Optional[AuthorizationScope] = None
    # Instead of giving them a raw ToolExecutor, we pass the KALIExecutor internally via the Manager,
    # but the context holds the request state.
    state: Dict[str, Any] = Field(default_factory=dict)

class AgentResult(BaseModel):
    """Standardized result from an agent execution."""
    agent_id: str
    success: bool
    output: str
    data: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None

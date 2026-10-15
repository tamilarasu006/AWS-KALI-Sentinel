from pydantic import BaseModel, Field
from typing import List, Optional

class AuthorizationScope(BaseModel):
    """
    Defines the authorized execution boundaries for high-risk tools.
    Cybersecurity tools, for example, must check this scope before running against a target.
    """
    allowed_targets: List[str] = Field(default_factory=list, description="List of IP addresses, domains, or subnets authorized for interaction")
    max_concurrent_connections: int = Field(default=10, description="Rate limit restriction")
    allow_destructive_actions: bool = Field(default=False, description="Whether destructive/modifying operations are permitted")
    
    def is_target_allowed(self, target: str) -> bool:
        # Simplified check. In a real system, this would parse CIDRs and domain wildcards.
        return target in self.allowed_targets

class ToolPermissionContext(BaseModel):
    """
    Complete context required to authorize tool execution for a specific user/task.
    Provides isolation and restricts tools from crossing boundaries.
    """
    user_id: str
    project_id: str
    task_id: str
    capabilities: List[str] = Field(default_factory=list)
    permissions: List[str] = Field(default_factory=list)
    authorization_scope: Optional[AuthorizationScope] = None
    risk_level: str = "LOW"


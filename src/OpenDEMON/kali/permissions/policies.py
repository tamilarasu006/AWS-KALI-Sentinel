"""High-level policy structures for KALI."""

from typing import List, Optional
from pydantic import BaseModel, Field

class PolicySummary(BaseModel):
    policy_id: str
    name: str
    allowed_tools: List[str] = Field(default_factory=list)
    denied_tools: List[str] = Field(default_factory=list)
    allowed_permissions: List[str] = Field(default_factory=list)
    denied_permissions: List[str] = Field(default_factory=list)

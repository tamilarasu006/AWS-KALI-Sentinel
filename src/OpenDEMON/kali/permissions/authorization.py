"""Authorization scope models for KALI."""

from pydantic import BaseModel, Field
from typing import List

class AuthorizationScope(BaseModel):
    """
    Explicit scope of authorization, usually granted externally for cybersecurity tools.
    """
    authorization_id: str
    allowed_targets: List[str] = Field(default_factory=list, description="List of authorized targets.")
    max_depth: int = Field(default=0)
    allow_destructive: bool = False
    
    def is_target_allowed(self, target: str) -> bool:
        # Simplified check. In a real system, this would parse CIDRs and domain wildcards.
        return target in self.allowed_targets

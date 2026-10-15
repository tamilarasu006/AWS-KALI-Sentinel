"""Models for KALI Internet Gateway."""
from typing import List, Optional, Dict
from pydantic import BaseModel, Field

class DomainPolicy(BaseModel):
    allowed_domains: List[str] = Field(default_factory=list, description="Explicit whitelist. If empty, all non-denied/non-private domains allowed.")
    denied_domains: List[str] = Field(default_factory=list, description="Explicit blacklist.")

class NetworkPolicy(BaseModel):
    max_redirects: int = 3
    timeout_seconds: float = 10.0
    max_response_bytes: int = 1024 * 1024 * 10 # 10MB default
    domain_policy: DomainPolicy = Field(default_factory=DomainPolicy)
    allow_http: bool = False # Strongly prefer HTTPS
    
class GatewayRequest(BaseModel):
    url: str
    method: str = "GET"
    headers: Dict[str, str] = Field(default_factory=dict)
    body: Optional[str] = None
    
class GatewayResponse(BaseModel):
    success: bool
    status_code: Optional[int] = None
    content: str = ""
    error: Optional[str] = None
    redirected_to: Optional[str] = None

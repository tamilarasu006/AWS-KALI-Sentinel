from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Optional

class RiskLevel(str, Enum):
    LOW = "LOW"             # Safe operations, local reading, basic math
    MEDIUM = "MEDIUM"       # Local file writes, controlled API requests
    HIGH = "HIGH"           # DB modifications, executing arbitrary code in sandbox
    CRITICAL = "CRITICAL"   # Unrestricted cyber ops, modifying root system, un-sandboxed code

class CapabilityCategory(str, Enum):
    GENERAL = "GENERAL"
    SOFTWARE = "SOFTWARE"
    DATA = "DATA"
    WEB = "WEB"
    DOCUMENTS = "DOCUMENTS"
    DEVOPS = "DEVOPS"
    GAME = "GAME"
    CYBERSECURITY = "CYBERSECURITY"
    AI_ML = "AI_ML"

class IORequirement(BaseModel):
    name: str
    description: str
    required: bool = True
    type: str = "string"

from pydantic import BaseModel, Field
from typing import List
from .schemas import CapabilityCategory, RiskLevel, IORequirement

class Capability(BaseModel):
    """
    Defines an abstract capability that KALI can perform.
    This acts as a bridge between a high-level task and the concrete tools/agents needed to execute it.
    """
    name: str = Field(..., description="Unique identifier for the capability (e.g., DATA_ANALYSIS)")
    description: str = Field(..., description="Human-readable description of what this capability does")
    category: CapabilityCategory
    
    inputs: List[IORequirement] = Field(default_factory=list, description="Expected inputs to perform this capability")
    outputs: List[IORequirement] = Field(default_factory=list, description="Expected outputs produced by this capability")
    
    required_tools: List[str] = Field(default_factory=list, description="List of tool names required to execute this capability")
    
    risk_level: RiskLevel = Field(default=RiskLevel.LOW, description="Inherent risk level of this capability")
    permission_requirements: List[str] = Field(default_factory=list, description="RBAC permissions required by the user to use this capability")

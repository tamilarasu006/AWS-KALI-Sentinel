from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class PlanStep(BaseModel):
    id: str
    description: str
    dependencies: List[str] = Field(default_factory=list)
    assigned_agent: str
    required_capabilities: List[str] = Field(default_factory=list)
    required_tools: List[str] = Field(default_factory=list)
    expected_outputs: List[str] = Field(default_factory=list)
    verification_criteria: str
    
    # Execution State
    status: str = "PENDING"  # PENDING, RUNNING, COMPLETED, FAILED
    result_output: Optional[str] = None
    error: Optional[str] = None

class Plan(BaseModel):
    goal: str
    steps: List[PlanStep] = Field(default_factory=list)
    status: str = "PENDING"
    
    def get_step(self, step_id: str) -> Optional[PlanStep]:
        for s in self.steps:
            if s.id == step_id:
                return s
        return None

class ExecutionResult(BaseModel):
    success: bool
    final_output: str
    plan: Plan
    errors: List[str] = Field(default_factory=list)

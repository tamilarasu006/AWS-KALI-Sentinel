from pydantic import BaseModel
from typing import List, Optional

class BenchmarkTask(BaseModel):
    task_id: str
    category: str
    prompt: str
    expected_capabilities: List[str]
    allowed_tools: List[str]
    expected_artifacts: Optional[List[str]] = []
    success_conditions: Optional[List[str]] = []
    validation_rules: Optional[List[str]] = []
    maximum_steps: int = 30
    maximum_tool_calls: int = 50
    maximum_runtime: int = 300
    safety_requirements: Optional[List[str]] = []
    requires_approval: bool = False
    difficulty: str = "medium"
    tags: List[str] = []
    dataset_version: str = "1.0.0"\n
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class ExecutionLimits:
    max_depth: int = 5
    max_retries: int = 3
    max_execution_time_sec: int = 3600
    max_child_tasks: int = 20
    max_tool_calls: int = 15

@dataclass
class TaskContext:
    user_id: str
    project_id: Optional[str]
    task_id: str
    permissions: List[str] = field(default_factory=list)
    available_capabilities: List[str] = field(default_factory=list)
    available_tools: List[str] = field(default_factory=list)
    memory_context: str = ""
    rag_context: str = ""
    environment_info: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[Dict[str, Any]] = field(default_factory=list)
    limits: ExecutionLimits = field(default_factory=ExecutionLimits)
    
    def sanitize(self) -> Dict[str, Any]:
        """Returns a safe dictionary representation without any sensitive data."""
        # Ensure no secrets or tokens are passed in environment_info
        safe_env = {k: v for k, v in self.environment_info.items() if "secret" not in k.lower() and "token" not in k.lower() and "key" not in k.lower()}
        
        return {
            "task_id": self.task_id,
            "project_id": self.project_id,
            "available_capabilities": self.available_capabilities,
            "available_tools": self.available_tools,
            "environment_info": safe_env
        }

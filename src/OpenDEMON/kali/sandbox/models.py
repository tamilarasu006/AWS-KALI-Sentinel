"""Data structures for KALI Sandbox execution."""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class ResourceLimits(BaseModel):
    """Limits applied to a sandbox execution."""
    max_cpu_percent: Optional[float] = Field(default=80.0, description="Max CPU usage percentage allowed.")
    max_memory_mb: Optional[int] = Field(default=512, description="Max memory in MB.")
    timeout_seconds: float = Field(default=30.0, description="Max execution time.")
    max_output_size_bytes: int = Field(default=1024 * 1024 * 5, description="Max combined stdout/stderr size (5MB).")
    max_processes: Optional[int] = Field(default=10, description="Max child processes.")

class SandboxConfig(BaseModel):
    """Configuration for the Sandbox Manager."""
    work_dir: Optional[str] = None
    limits: ResourceLimits = Field(default_factory=ResourceLimits)
    allow_network: bool = False
    allowed_env_vars: List[str] = Field(default_factory=list)

class SandboxRequest(BaseModel):
    """A request to execute code in the sandbox."""
    language: str = Field(..., description="E.g., python, node, bash")
    code: str = Field(..., description="The code to execute.")
    dependencies: List[str] = Field(default_factory=list)
    files: Dict[str, str] = Field(default_factory=dict, description="Files to write into the sandbox workspace before execution.")
    timeout_override: Optional[float] = None

class SandboxResult(BaseModel):
    """The result of a sandbox execution."""
    success: bool
    exit_code: Optional[int] = None
    stdout: str = ""
    stderr: str = ""
    duration_seconds: float = 0.0
    error: Optional[str] = None
    artifacts: Dict[str, bytes] = Field(default_factory=dict, description="Files generated/modified in the workspace.")

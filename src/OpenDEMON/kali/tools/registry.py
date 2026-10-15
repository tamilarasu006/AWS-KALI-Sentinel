import asyncio
from typing import Dict, Optional, Type, List, Any
from pydantic import BaseModel, Field

from OpenDEMON.kali.tools.tool import KaliTool
from OpenDEMON.kali.permissions.authorization import AuthorizationScope
from OpenDEMON.kali.permissions.risk import RiskLevel

# ---------------------------------------------------------
# Tool Input/Output Schemas
# ---------------------------------------------------------
class EmptyInput(BaseModel): pass
class GenericStringOutput(BaseModel): result: str

class CyberTargetInput(BaseModel):
    target: str = Field(..., description="Target IP or Domain")

class CyberTargetOutput(BaseModel):
    findings: str

# ---------------------------------------------------------
# Mock Tool Implementations
# ---------------------------------------------------------
class MockWebSearchTool(KaliTool):
    name: str = "web_search"
    description: str = "Searches the web"
    input_schema: Type[BaseModel] = EmptyInput
    output_schema: Type[BaseModel] = GenericStringOutput
    required_capability: str = "WEB_SEARCH"
    risk_level: RiskLevel = RiskLevel.LOW
    
    async def execute(self, inputs: BaseModel, auth_scope: AuthorizationScope = None) -> BaseModel:
        return GenericStringOutput(result="Search results mock")

class MockPythonEvalTool(KaliTool):
    name: str = "python_eval"
    description: str = "Evaluates Python code"
    input_schema: Type[BaseModel] = EmptyInput
    output_schema: Type[BaseModel] = GenericStringOutput
    required_capability: str = "PYTHON_DEVELOPMENT"
    risk_level: RiskLevel = RiskLevel.MEDIUM
    
    async def execute(self, inputs: BaseModel, auth_scope: AuthorizationScope = None) -> BaseModel:
        return GenericStringOutput(result="Python exec mock")

class MockAuthReconTool(KaliTool):
    name: str = "auth_recon"
    description: str = "Performs authorized reconnaissance on a target"
    input_schema: Type[BaseModel] = CyberTargetInput
    output_schema: Type[BaseModel] = CyberTargetOutput
    required_capability: str = "AUTHORIZED_RECONNAISSANCE"
    risk_level: RiskLevel = RiskLevel.CRITICAL
    permissions: List[str] = ["security:audit"]
    
    async def execute(self, inputs: CyberTargetInput, auth_scope: AuthorizationScope = None) -> BaseModel:
        if not auth_scope or not auth_scope.is_target_allowed(inputs.target):
            raise PermissionError(f"Target {inputs.target} is not in the authorized scope.")
        return CyberTargetOutput(findings=f"Recon findings for {inputs.target}")

class MockTimeoutTool(KaliTool):
    name: str = "timeout_tool"
    description: str = "A tool that always times out"
    input_schema: Type[BaseModel] = EmptyInput
    output_schema: Type[BaseModel] = GenericStringOutput
    required_capability: str = "REASONING"
    risk_level: RiskLevel = RiskLevel.LOW
    timeout: float = 0.1
    
    async def execute(self, inputs: BaseModel, auth_scope: AuthorizationScope = None) -> BaseModel:
        await asyncio.sleep(0.5)
        return GenericStringOutput(result="Done")

# ---------------------------------------------------------
# Registry
# ---------------------------------------------------------
class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, KaliTool] = {}
        self._load_defaults()
        
    def register(self, tool: KaliTool, replace: bool = False):
        """Registers a tool. Prevents duplicates unless replace=True."""
        if tool.name in self._tools and not replace:
            raise ValueError(f"Tool '{tool.name}' is already registered.")
        self._tools[tool.name] = tool
        
    def unregister(self, name: str):
        if name in self._tools:
            del self._tools[name]
            
    def get(self, name: str) -> Optional[KaliTool]:
        return self._tools.get(name)
        
    def list(self) -> List[KaliTool]:
        return list(self._tools.values())
        
    def exists(self, name: str) -> bool:
        return name in self._tools
        
    def find_by_category(self, category: str) -> List[KaliTool]:
        return [t for t in self._tools.values() if t.category == category]
        
    def find_by_capability(self, capability: str) -> List[KaliTool]:
        return [t for t in self._tools.values() if t.required_capability == capability]
        
    def find_by_permission(self, permission: str) -> List[KaliTool]:
        return [t for t in self._tools.values() if permission in t.permissions]
        
    def search(self, query: str) -> List[KaliTool]:
        query = query.lower()
        return [t for t in self._tools.values() if query in t.name.lower() or query in t.description.lower()]
        
    def enable(self, name: str):
        if name in self._tools:
            self._tools[name].enabled = True
            
    def disable(self, name: str):
        if name in self._tools:
            self._tools[name].enabled = False
            
    def clear(self):
        self._tools.clear()
        
    def health_all(self) -> Dict[str, Dict[str, Any]]:
        return {name: tool.health() for name, tool in self._tools.items()}
        
    def _load_defaults(self):
        self.register(MockWebSearchTool())
        self.register(MockPythonEvalTool())
        self.register(MockAuthReconTool())
        self.register(MockTimeoutTool())

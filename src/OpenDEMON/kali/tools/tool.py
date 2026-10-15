from pydantic import BaseModel, Field
from typing import Type, List, Any, Dict
from abc import ABC, abstractmethod
from OpenDEMON.kali.permissions.risk import RiskLevel
from OpenDEMON.kali.permissions.authorization import AuthorizationScope

class KaliTool(ABC, BaseModel):
    """
    Abstract base class for all tools executable by KALI.
    """
    name: str
    description: str
    category: str = "general"
    version: str = "1.0.0"
    
    # Schemas must be defined by concrete implementations
    input_schema: Type[BaseModel]
    output_schema: Type[BaseModel]
    
    required_capability: str
    risk_level: RiskLevel
    permissions: List[str] = Field(default_factory=list)
    
    timeout: float = Field(default=30.0, description="Execution timeout in seconds")
    resource_limits: Dict[str, Any] = Field(default_factory=dict, description="Resource bounds (e.g. max memory)")
    
    enabled: bool = True
    execution_mode: str = "async"
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def validate_input(self, inputs: Dict[str, Any]) -> BaseModel:
        """Validates raw dictionary input against the input_schema."""
        return self.input_schema(**inputs)

    def validate_output(self, output: Any) -> BaseModel:
        """Validates tool execution output against the output_schema."""
        if isinstance(output, self.output_schema):
            return output
        if isinstance(output, dict):
            return self.output_schema(**output)
        return self.output_schema(**(output.dict() if hasattr(output, 'dict') else {}))
        
    def health(self) -> Dict[str, Any]:
        """Returns health information about the tool's availability."""
        return {
            "name": self.name,
            "enabled": self.enabled,
            "status": "healthy" if self.enabled else "disabled",
            "version": self.version
        }

    @abstractmethod
    async def execute(self, inputs: BaseModel, auth_scope: AuthorizationScope = None) -> BaseModel:
        """
        Executes the tool logic.
        :param inputs: A validated Pydantic model matching `input_schema`.
        :param auth_scope: The authorization boundaries for the request.
        :return: A Pydantic model matching `output_schema`.
        """
        pass

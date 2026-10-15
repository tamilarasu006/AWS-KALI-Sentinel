from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from OpenDEMON.kali.agents.models import AgentContext, AgentResult, AgentCapabilities
from OpenDEMON.kali.permissions.risk import RiskLevel

class AgentBase(ABC):
    """Base interface for all KALI Specialized Agents."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
        
    @property
    @abstractmethod
    def description(self) -> str:
        pass
        
    @property
    @abstractmethod
    def capabilities(self) -> AgentCapabilities:
        pass
        
    @property
    @abstractmethod
    def allowed_tools(self) -> List[str]:
        pass
        
    @property
    @abstractmethod
    def risk_level(self) -> RiskLevel:
        pass
        
    @property
    @abstractmethod
    def input_schema(self) -> Dict[str, Any]:
        """JSON Schema for expected inputs."""
        pass
        
    @property
    @abstractmethod
    def output_schema(self) -> Dict[str, Any]:
        """JSON Schema for expected outputs."""
        pass

    @abstractmethod
    async def execute(self, prompt: str, context: AgentContext, executor: Any = None) -> AgentResult:
        """
        Executes the specialized task.
        The 'executor' is expected to be a KALIExecutor instance provided by the AgentManager,
        guaranteeing it honors permissions, sandbox, and internet gateway rules.
        """
        pass

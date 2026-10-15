from typing import Dict, Any, List, Optional
from OpenDEMON.kali.agents.base_agent import AgentBase
from OpenDEMON.kali.agents.models import AgentContext, AgentResult, AgentCapabilities
from OpenDEMON.kali.permissions.risk import RiskLevel

class BaseSpecialist(AgentBase):
    """Utility class to reduce boilerplate for specialist agents."""
    
    def __init__(self, name: str, description: str, caps: AgentCapabilities, allowed: List[str], risk: RiskLevel):
        self._name = name
        self._desc = description
        self._caps = caps
        self._allowed = allowed
        self._risk = risk
        
    @property
    def name(self) -> str: return self._name
    @property
    def description(self) -> str: return self._desc
    @property
    def capabilities(self) -> AgentCapabilities: return self._caps
    @property
    def allowed_tools(self) -> List[str]: return self._allowed
    @property
    def risk_level(self) -> RiskLevel: return self._risk
    @property
    def input_schema(self) -> Dict[str, Any]: return {"type": "object", "properties": {"prompt": {"type": "string"}}}
    @property
    def output_schema(self) -> Dict[str, Any]: return {"type": "object", "properties": {"output": {"type": "string"}}}

    async def execute(self, prompt: str, context: AgentContext, executor: Any = None) -> AgentResult:
        return AgentResult(
            agent_id=self.name,
            success=True,
            output=f"[{self.name}] Executed prompt: {prompt}"
        )

# 1. GeneralAgent
class GeneralAgent(BaseSpecialist):
    def __init__(self):
        super().__init__(
            "GeneralAgent", "Handles general purpose queries and routing.",
            AgentCapabilities(primary_domain="general", supported_tasks=["chat", "summarize", "qa"]),
            ["web_search", "read_file"], RiskLevel.LOW
        )

# 2. SoftwareAgent
class SoftwareAgent(BaseSpecialist):
    def __init__(self):
        super().__init__(
            "SoftwareAgent", "Writes and refactors code.",
            AgentCapabilities(primary_domain="software_engineering", supported_tasks=["coding", "debugging", "refactoring"]),
            ["read_file", "write_file", "execute_code"], RiskLevel.MEDIUM
        )

# 3. DataAgent
class DataAgent(BaseSpecialist):
    def __init__(self):
        super().__init__(
            "DataAgent", "Analyzes data and structures datasets.",
            AgentCapabilities(primary_domain="data_science", supported_tasks=["analysis", "etl", "visualization"]),
            ["read_file", "write_file", "run_python", "execute_code"], RiskLevel.MEDIUM
        )

# 4. ResearchAgent
class ResearchAgent(BaseSpecialist):
    def __init__(self):
        super().__init__(
            "ResearchAgent", "Performs deep internet research.",
            AgentCapabilities(primary_domain="research", supported_tasks=["search", "summarize", "fact_check"]),
            ["web_search", "browse_web", "download_file"], RiskLevel.LOW
        )

# 5. CyberAgent
class CyberAgent(BaseSpecialist):
    def __init__(self):
        super().__init__(
            "CyberAgent", "Performs authorized cybersecurity operations.",
            AgentCapabilities(primary_domain="cybersecurity", supported_tasks=["recon", "scanning", "exploitation"], restricted=True),
            ["execute_shell", "run_script", "nmap_scan"], RiskLevel.HIGH
        )
        
    async def execute(self, prompt: str, context: AgentContext, executor: Any = None) -> AgentResult:
        # CyberAgent explicitly demands AuthorizationScope
        if not context.auth_scope:
            return AgentResult(
                agent_id=self.name,
                success=False,
                output="",
                error="CyberAgent requires an explicit AuthorizationScope in context. Missing authorization."
            )
            
        return await super().execute(prompt, context, executor)

# 6. GameAgent
class GameAgent(BaseSpecialist):
    def __init__(self):
        super().__init__(
            "GameAgent", "Designs and implements game logic.",
            AgentCapabilities(primary_domain="gamedev", supported_tasks=["mechanics", "level_design", "ai"]),
            ["read_file", "write_file", "run_python"], RiskLevel.LOW
        )

# 7. DevOpsAgent
class DevOpsAgent(BaseSpecialist):
    def __init__(self):
        super().__init__(
            "DevOpsAgent", "Manages infrastructure and deployments.",
            AgentCapabilities(primary_domain="devops", supported_tasks=["ci_cd", "docker", "cloud"]),
            ["execute_shell", "read_file", "write_file"], RiskLevel.HIGH
        )

# 8. AIEngineeringAgent
class AIEngineeringAgent(BaseSpecialist):
    def __init__(self):
        super().__init__(
            "AIEngineeringAgent", "Builds and tunes AI models.",
            AgentCapabilities(primary_domain="machine_learning", supported_tasks=["training", "inference", "prompt_engineering"]),
            ["run_python", "read_file", "write_file"], RiskLevel.MEDIUM
        )

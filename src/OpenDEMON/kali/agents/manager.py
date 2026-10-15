from typing import List, Optional, Any
from OpenDEMON.kali.agents.registry import AgentRegistry
from OpenDEMON.kali.agents.base_agent import AgentBase
from OpenDEMON.kali.agents.models import AgentContext, AgentResult
from OpenDEMON.kali.orchestration.executor import KALIExecutor

class AgentManager:
    """Manages the routing and secure execution of specialized KALI agents."""
    
    def __init__(self, registry: AgentRegistry, executor: KALIExecutor):
        self.registry = registry
        self.executor = executor
        
    def register(self, agent: AgentBase):
        self.registry.register(agent)
        
    def get(self, name: str) -> Optional[AgentBase]:
        return self.registry.get(name)
        
    def list(self) -> List[AgentBase]:
        return self.registry.list_agents()
        
    def find_by_capability(self, capability: str) -> List[AgentBase]:
        return self.registry.find_by_capability(capability)
        
    def select_agent(self, task_description: str) -> Optional[AgentBase]:
        """Naively selects the best agent. In a full system, an LLM router could be used."""
        words = set(task_description.lower().split())
        for agent in self.list():
            if agent.name == "GeneralAgent":
                continue # Evaluate general last
            domain_words = set(agent.capabilities.primary_domain.lower().replace("_", " ").split())
            if words.intersection(domain_words):
                return agent
            for task in agent.capabilities.supported_tasks:
                task_words = set(task.lower().replace("_", " ").split())
                if words.intersection(task_words):
                    return agent
        return self.get("GeneralAgent")
        
    async def execute_agent(self, agent_name: str, prompt: str, context: AgentContext) -> AgentResult:
        """
        Executes a specialized agent, injecting the secure KALIExecutor.
        This guarantees the agent must pass through the Permission Manager,
        Sandbox, and Internet Gateway for any tool calls.
        """
        agent = self.get(agent_name)
        if not agent:
            return AgentResult(
                agent_id=agent_name,
                success=False,
                output="",
                error=f"Agent '{agent_name}' not found."
            )
            
        try:
            return await agent.execute(prompt, context, self.executor)
        except Exception as e:
            return AgentResult(
                agent_id=agent_name,
                success=False,
                output="",
                error=str(e)
            )

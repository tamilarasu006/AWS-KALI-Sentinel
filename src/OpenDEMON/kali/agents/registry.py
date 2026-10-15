from typing import Dict, List, Optional, Type
from OpenDEMON.kali.agents.base_agent import AgentBase

class AgentRegistry:
    """Central registry for all KALI specialized agents."""
    
    def __init__(self):
        self._agents: Dict[str, AgentBase] = {}
        
    def register(self, agent: AgentBase):
        """Registers a single agent."""
        self._agents[agent.name] = agent
        
    def get(self, name: str) -> Optional[AgentBase]:
        """Retrieves an agent by name."""
        return self._agents.get(name)
        
    def list_agents(self) -> List[AgentBase]:
        """Lists all registered agents."""
        return list(self._agents.values())
        
    def find_by_capability(self, capability: str) -> List[AgentBase]:
        """Finds agents supporting a specific capability."""
        matches = []
        for agent in self._agents.values():
            if capability.lower() in agent.capabilities.primary_domain.lower() or \
               any(capability.lower() in t.lower() for t in agent.capabilities.supported_tasks):
                matches.append(agent)
        return matches

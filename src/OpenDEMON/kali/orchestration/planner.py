from dataclasses import dataclass
from typing import List, Optional

@dataclass
class ExecutionPlan:
    requires_rag: bool
    requires_tools: bool
    required_memory_types: List[str]
    tool_names: List[str]
    target_agents: List[str]
    is_simple_chat: bool

class KALIPlanner:
    """Analyzes user requests and constructs a Multi-Agent ExecutionPlan."""
    
    def __init__(self, available_tools: List[str] = None):
        self.available_tools = available_tools or []

    def plan(self, request_text: str) -> ExecutionPlan:
        """
        Determines the multi-agent requirements for fulfilling a request.
        """
        req_lower = request_text.lower()
        
        requires_rag = False
        requires_tools = False
        tool_names = []
        target_agents = []
        memory_types = ["short_term"]

        # RAG and Memory heuristics
        if any(kw in req_lower for kw in ["document", "file", "search knowledge", "according to the doc"]):
            requires_rag = True
            memory_types.append("semantic")

        if any(kw in req_lower for kw in ["remember", "recall", "what did i say"]):
            memory_types.append("long_term")
            memory_types.append("episodic")

        # KALI Intelligence - Multi-Agent Task Decomposition (Heuristic Simulation)
        if any(kw in req_lower for kw in ["code", "react", "node", "python", "debug"]):
            target_agents.append("kali_software_agent")
            requires_tools = True
            tool_names.append("execute_python")
            
        if any(kw in req_lower for kw in ["data", "sql", "analyze", "plot", "pandas"]):
            target_agents.append("kali_data_agent")
            requires_tools = True
            tool_names.append("execute_python")

        if any(kw in req_lower for kw in ["security", "scan", "vulnerability", "nmap", "hack"]):
            target_agents.append("kali_cyber_agent")
            requires_tools = True
            tool_names.append("run_nmap")

        is_simple_chat = not requires_rag and not requires_tools and not target_agents and len(memory_types) == 1

        return ExecutionPlan(
            requires_rag=requires_rag,
            requires_tools=requires_tools,
            required_memory_types=memory_types,
            tool_names=tool_names,
            target_agents=target_agents,
            is_simple_chat=is_simple_chat
        )

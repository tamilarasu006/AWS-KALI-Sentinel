"""KALI Multi-Agent System"""
from OpenDEMON.kali.agents.models import AgentContext, AgentCapabilities, AgentResult
from OpenDEMON.kali.agents.base_agent import AgentBase
from OpenDEMON.kali.agents.registry import AgentRegistry
from OpenDEMON.kali.agents.manager import AgentManager
from OpenDEMON.kali.agents.specialists import (
    GeneralAgent, SoftwareAgent, DataAgent, ResearchAgent,
    CyberAgent, GameAgent, DevOpsAgent, AIEngineeringAgent
)

__all__ = [
    "AgentContext",
    "AgentCapabilities",
    "AgentResult",
    "AgentBase",
    "AgentRegistry",
    "AgentManager",
    "GeneralAgent",
    "SoftwareAgent",
    "DataAgent",
    "ResearchAgent",
    "CyberAgent",
    "GameAgent",
    "DevOpsAgent",
    "AIEngineeringAgent"
]

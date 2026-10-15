import json
import logging
from typing import Dict, Any, List, Optional
from OpenDEMON.engine._stubs import InferenceEngine
from OpenDEMON.core.types import Message, Role

from OpenDEMON.kali.capabilities.registry import CapabilityRegistry
from OpenDEMON.kali.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)

class KALIPlanner:
    """
    LLM-driven planner that translates high-level objectives into 
    executable tool commands by leveraging the KALI Capability and Tool Registries.
    """
    
    def __init__(self, engine: InferenceEngine, model: str, capability_registry: CapabilityRegistry, tool_registry: ToolRegistry):
        self.engine = engine
        self.model = model
        self.capability_registry = capability_registry
        self.tool_registry = tool_registry

    def _build_system_prompt(self) -> str:
        # Provide the LLM with the list of capabilities and available tools
        capabilities = self.capability_registry.get_all()
        tools = self.tool_registry.list()
        
        prompt = (
            "You are KALI (Knowledge and Logic Interface), an advanced agentic orchestrator.\n"
            "Your task is to analyze the user's objective and generate a JSON plan of execution.\n\n"
            "AVAILABLE CAPABILITIES:\n"
        )
        for cap in capabilities:
            prompt += f"- {cap.name}: {cap.description} (Risk: {cap.risk_level.value})\n"
            
        prompt += "\nAVAILABLE TOOLS:\n"
        for tool in tools:
            # We assume tool has name, description, required_capability
            prompt += f"- {tool.name}: {tool.description} (Requires Capability: {tool.required_capability})\n"
            if hasattr(tool, "input_schema"):
                prompt += f"  Schema: {tool.input_schema.model_json_schema() if hasattr(tool.input_schema, 'model_json_schema') else tool.input_schema}\n"
                
        prompt += (
            "\nBased on the user's request, you must respond strictly with a JSON object containing a 'plan'. "
            "The 'plan' is a list of steps. Each step must include:\n"
            "- 'step_name': A short description.\n"
            "- 'capability': The capability required.\n"
            "- 'tool': The name of the tool to use.\n"
            "- 'inputs': A dictionary of inputs matching the tool's schema.\n\n"
            "Respond ONLY with valid JSON. Do not include markdown formatting or reasoning outside the JSON."
        )
        return prompt

    def generate_plan(self, objective: str) -> Dict[str, Any]:
        """
        Calls the LLM to generate a plan for the given objective.
        Returns the parsed JSON plan.
        """
        system_prompt = self._build_system_prompt()
        messages = [
            Message(role=Role.SYSTEM, content=system_prompt),
            Message(role=Role.USER, content=objective)
        ]
        
        logger.info(f"Generating KALI plan for objective: {objective}")
        try:
            result = self.engine.generate(messages, model=self.model, temperature=0.2)
            content = result.get("content", "").strip()
            
            # Strip markdown if present
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
                
            plan_data = json.loads(content.strip())
            return plan_data
            
        except Exception as e:
            logger.error(f"Failed to generate plan: {e}")
            raise RuntimeError(f"KALI Planner failed: {e}")

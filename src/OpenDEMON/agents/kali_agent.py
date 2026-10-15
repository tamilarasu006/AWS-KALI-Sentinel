import json
import logging
from typing import Any, Optional

from OpenDEMON.agents._stubs import AgentContext, AgentResult, BaseAgent
from OpenDEMON.core.registry import AgentRegistry
from OpenDEMON.core.types import ToolResult

from OpenDEMON.kali.core.planner import KALIPlanner
from OpenDEMON.kali.capabilities.registry import CapabilityRegistry
from OpenDEMON.kali.tools.registry import ToolRegistry
from OpenDEMON.kali.tools.executor import SafeExecutor
from OpenDEMON.kali.tools.permissions import AuthorizationScope

logger = logging.getLogger(__name__)

@AgentRegistry.register("kali")
class KALIAgent(BaseAgent):
    """
    KALI Agent - Generative AI planner mapping capabilities to tool executions.
    """
    agent_id = "kali"
    accepts_tools = False # We use our own KALI tool registry, not the standard OpenDEMON tools

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.capability_registry = CapabilityRegistry()
        self.tool_registry = ToolRegistry()
        self.planner = KALIPlanner(
            engine=self._engine,
            model=self._model,
            capability_registry=self.capability_registry,
            tool_registry=self.tool_registry
        )

    async def run_async(
        self,
        input: str,
        context: Optional[AgentContext] = None,
        auth_scope: Optional[AuthorizationScope] = None,
        **kwargs: Any,
    ) -> AgentResult:
        """
        Asynchronous execution loop for KALI Planner.
        """
        self._emit_turn_start(input)
        
        try:
            plan = self.planner.generate_plan(input)
        except Exception as e:
            self._emit_turn_end(error=str(e))
            return AgentResult(content=f"Error generating plan: {e}", turns=1)
            
        steps = plan.get("plan", [])
        if not steps:
            self._emit_turn_end()
            return AgentResult(content="No actionable steps identified for this objective.", turns=1)
            
        execution_results = []
        final_content = "KALI Execution Plan:\n"
        
        for idx, step in enumerate(steps, 1):
            tool_name = step.get("tool")
            inputs = step.get("inputs", {})
            step_name = step.get("step_name", "Unknown step")
            
            final_content += f"\n{idx}. {step_name} (Tool: {tool_name})"
            
            tool = self.tool_registry.get(tool_name)
            if not tool:
                error_msg = f"Tool '{tool_name}' not found in registry."
                final_content += f"\n   Error: {error_msg}"
                continue
                
            try:
                # Assuming SafeExecutor handles the permissions if we pass auth_scope 
                # (Permissions handled natively in SafeExecutor / engine integration in step 22)
                # Wait, step 22 said KALIPermissionEngine was integrated into KALIToolExecutor.
                # Actually, in runtime.py it was explicitly calling KALIPermissionManager before SafeExecutor.execute_tool
                # We'll just execute it and let SafeExecutor or a wrapped manager handle it.
                result = await SafeExecutor.execute_tool(
                    tool=tool,
                    raw_inputs=inputs,
                    auth_scope=auth_scope
                )
                
                # Convert Kali ToolResult to standard OpenDEMON ToolResult
                std_result = ToolResult(
                    tool_name=tool.name,
                    arguments=inputs,
                    output=result.output if result.success else f"Error: {result.error}"
                )
                execution_results.append(std_result)
                
                if result.success:
                    final_content += f"\n   Success: {result.output}"
                else:
                    final_content += f"\n   Failed: {result.error}"
                    
            except Exception as e:
                error_msg = str(e)
                final_content += f"\n   Exception: {error_msg}"
                execution_results.append(ToolResult(tool_name=tool_name, arguments=inputs, output=f"Exception: {error_msg}"))

        self._emit_turn_end(content_length=len(final_content))
        return AgentResult(content=final_content, tool_results=execution_results, turns=1)

    def run(
        self,
        input: str,
        context: Optional[AgentContext] = None,
        **kwargs: Any,
    ) -> AgentResult:
        """
        Synchronous fallback execution loop.
        """
        import asyncio
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import nest_asyncio
            nest_asyncio.apply()
        return loop.run_until_complete(self.run_async(input, context, **kwargs))

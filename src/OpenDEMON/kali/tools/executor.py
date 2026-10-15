import asyncio
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, TYPE_CHECKING
from OpenDEMON.kali.tools.tool import KaliTool
from OpenDEMON.kali.tools.results import ToolResult
from OpenDEMON.kali.permissions.authorization import AuthorizationScope
from OpenDEMON.kali.permissions.risk import RiskLevel

if TYPE_CHECKING:
    from OpenDEMON.kali.core.events import EventManager

class SafeExecutor:
    """
    Wraps tool execution to ensure schemas are validated, timeouts are enforced,
    and authorization scopes are respected.
    Prevents arbitrary un-sandboxed shell execution directly from LLM text.
    """
    
    @staticmethod
    async def execute_tool(
        tool: KaliTool, 
        raw_inputs: Dict[str, Any], 
        auth_scope: Optional[AuthorizationScope] = None,
        event_manager: Optional['EventManager'] = None,
        task_id: Optional[str] = None
    ) -> ToolResult:
        start_time = time.time()
        start_dt = datetime.now(timezone.utc)
        execution_id = str(uuid.uuid4())
        
        from OpenDEMON.kali.core.events import EventType
        
        if event_manager and task_id:
            await event_manager.dispatch(task_id, EventType.TOOL_SELECTED, f"Selected tool {tool.name}")
            
        try:
            if not tool.enabled:
                raise ValueError(f"Tool {tool.name} is currently disabled.")
                
            # 1. Enforce Authorization requirements
            if tool.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL] and not auth_scope:
                raise PermissionError(f"Tool {tool.name} requires an AuthorizationScope due to risk level {tool.risk_level.name}")
                
            # 2. Validate Inputs
            validated_inputs = tool.validate_input(raw_inputs)
            
            if event_manager and task_id:
                await event_manager.dispatch(task_id, EventType.TOOL_STARTED, f"Starting tool {tool.name}")
            
            # 3. Execute with Timeout
            raw_output = await asyncio.wait_for(
                tool.execute(validated_inputs, auth_scope),
                timeout=tool.timeout
            )
            
            # 4. Validate Outputs
            validated_output = tool.validate_output(raw_output)
                
            elapsed = time.time() - start_time
            result = ToolResult(
                success=True,
                tool_name=tool.name,
                execution_id=execution_id,
                output=validated_output,
                started_at=start_dt,
                completed_at=datetime.now(timezone.utc),
                duration=elapsed
            )
            
            if event_manager and task_id:
                await event_manager.dispatch(task_id, EventType.TOOL_COMPLETED, f"Tool {tool.name} completed successfully")
                
            return result
            
        except asyncio.TimeoutError:
            elapsed = time.time() - start_time
            result = ToolResult(
                success=False,
                tool_name=tool.name,
                execution_id=execution_id,
                output=None,
                error=f"Tool execution timed out after {tool.timeout}s",
                started_at=start_dt,
                completed_at=datetime.now(timezone.utc),
                duration=elapsed
            )
            if event_manager and task_id:
                await event_manager.dispatch(task_id, EventType.TOOL_FAILED, f"Tool {tool.name} timed out")
            return result
            
        except Exception as e:
            elapsed = time.time() - start_time
            result = ToolResult(
                success=False,
                tool_name=tool.name,
                execution_id=execution_id,
                output=None,
                error=str(e),
                started_at=start_dt,
                completed_at=datetime.now(timezone.utc),
                duration=elapsed
            )
            if event_manager and task_id:
                await event_manager.dispatch(task_id, EventType.TOOL_FAILED, f"Tool {tool.name} failed: {str(e)}")
            return result

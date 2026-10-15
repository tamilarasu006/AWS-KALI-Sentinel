from typing import Any, Optional, Dict
from OpenDEMON.tools._stubs import ToolExecutor
from OpenDEMON.core.types import ToolCall, ToolResult
from OpenDEMON.kali.permissions.manager import KALIPermissionManager
from OpenDEMON.kali.permissions.authorization import AuthorizationScope
from OpenDEMON.kali.tools.tool import KaliTool

class KALIExecutor:
    """Wraps the existing OpenDEMON ToolExecutor to maintain native security boundaries."""
    
    def __init__(self, open_demon_executor: ToolExecutor, permission_manager: Optional[KALIPermissionManager] = None):
        self.tool_executor = open_demon_executor
        self.permission_manager = permission_manager

    async def execute_tool_async(
        self, 
        tool_call: ToolCall, 
        user_id: str = "system", 
        project_id: str = "system", 
        task_id: str = "system", 
        auth_scope: Optional[AuthorizationScope] = None
    ) -> ToolResult:
        """
        Executes a tool call natively through the OpenDEMON infrastructure,
        routing it through the KALIPermissionManager first.
        """
        if self.permission_manager:
            # We need to map ToolCall to KaliTool logic.
            # For this MVP integration, we lookup the tool metadata from the executor.
            tool_metadata = self.tool_executor._tools.get(tool_call.name)
            
            if not tool_metadata:
                return ToolResult(
                    tool_call_id=tool_call.id,
                    content="DENY: Unknown tool",
                    is_error=True
                )
                
            # If tool_metadata is not a KaliTool, wrap it so check_permission doesn't crash
            if not isinstance(tool_metadata, KaliTool):
                # Fallback mapping if it's just a dict or basic object
                from OpenDEMON.kali.permissions.risk import RiskLevel
                risk = getattr(tool_metadata, "risk_level", RiskLevel.MEDIUM)
                if isinstance(risk, str):
                    try:
                        risk = RiskLevel(risk)
                    except ValueError:
                        risk = RiskLevel.MEDIUM
                        
                kali_tool = KaliTool(
                    name=getattr(tool_metadata, "name", tool_call.name),
                    description=getattr(tool_metadata, "description", ""),
                    category=getattr(tool_metadata, "category", "general"),
                    risk_level=risk,
                    enabled=getattr(tool_metadata, "enabled", True)
                )
            else:
                kali_tool = tool_metadata

            # Check permissions
            inputs = tool_call.arguments if isinstance(tool_call.arguments, dict) else {}
            decision = await self.permission_manager.check_permission(
                user_id=user_id,
                project_id=project_id,
                task_id=task_id,
                tool=kali_tool,
                inputs=inputs,
                auth_scope=auth_scope
            )
            
            if not decision.allowed:
                return ToolResult(
                    tool_call_id=tool_call.id,
                    content=f"{decision.decision}: {decision.reason}",
                    is_error=True
                )

        # Proceed to execution
        # Check if this tool is a code execution tool that needs sandboxing
        if tool_call.name in ("execute_code", "run_script", "run_python", "run_node", "execute_shell"):
            from OpenDEMON.kali.sandbox.manager import SandboxManager
            from OpenDEMON.kali.sandbox.models import SandboxRequest
            
            manager = SandboxManager()
            
            # Map tool arguments to SandboxRequest
            args = tool_call.arguments if isinstance(tool_call.arguments, dict) else {}
            language = args.get("language", "python")
            code = args.get("code", "")
            
            request = SandboxRequest(
                language=language,
                code=code,
                files=args.get("files", {})
            )
            
            result = await manager.execute(request)
            
            content = f"Exit Code: {result.exit_code}\nStdout:\n{result.stdout}\nStderr:\n{result.stderr}"
            if result.error:
                content += f"\nSandbox Error: {result.error}"
                
            return ToolResult(
                tool_call_id=tool_call.id,
                content=content,
                is_error=not result.success
            )

        # Check if this tool is an internet gateway tool
        if tool_call.name in ("http_get", "web_search", "download_file", "browse_web"):
            from OpenDEMON.kali.internet.gateway import InternetGateway
            from OpenDEMON.kali.internet.models import GatewayRequest
            
            gateway = InternetGateway()
            args = tool_call.arguments if isinstance(tool_call.arguments, dict) else {}
            
            if tool_call.name == "web_search":
                query = args.get("query", "")
                result = await gateway.web_search(query)
            else:
                url = args.get("url", "")
                method = "GET" if tool_call.name == "http_get" else args.get("method", "GET")
                req = GatewayRequest(url=url, method=method)
                result = await gateway.process_http_request(req)
                
            content = f"Status Code: {result.status_code}\n" if result.status_code else ""
            if result.redirected_to:
                content += f"Redirected to: {result.redirected_to}\n"
            content += f"Response:\n{result.content}"
            if result.error:
                content += f"\nGateway Error: {result.error}"
                
            return ToolResult(
                tool_call_id=tool_call.id,
                content=content,
                is_error=not result.success
            )

        # Fallback to native tool execution
        return self.tool_executor.execute(tool_call)

    def execute_tool(self, tool_call: ToolCall) -> ToolResult:
        """
        Synchronous wrapper. In a real environment with permissions, 
        use execute_tool_async instead.
        """
        if self.permission_manager:
            return ToolResult(
                tool_call_id=tool_call.id,
                content="DENY: Synchronous tool execution is blocked when permission manager is enabled.",
                is_error=True
            )
        return self.tool_executor.execute(tool_call)

    def get_available_tool_descriptions(self) -> str:
        """Exposes tool descriptions for the KALI prompt."""
        from OpenDEMON.tools._stubs import build_tool_descriptions
        tools = list(self.tool_executor._tools.values())
        return build_tool_descriptions(tools)

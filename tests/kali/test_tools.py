import pytest
from pydantic import ValidationError
from OpenDEMON.kali.tools.registry import ToolRegistry
from OpenDEMON.kali.tools.executor import SafeExecutor
from OpenDEMON.kali.tools.permissions import AuthorizationScope

def test_registry_lookups():
    registry = ToolRegistry()
    assert registry.exists("web_search")
    assert not registry.exists("unknown_tool")
    
    # Capability lookup
    code_tools = registry.find_by_capability("PYTHON_DEVELOPMENT")
    assert len(code_tools) == 1
    assert code_tools[0].name == "python_eval"
    
    # Category lookup
    general_tools = registry.find_by_category("general")
    assert len(general_tools) > 0
    
    # Duplicate registration prevention
    from OpenDEMON.kali.tools.registry import MockWebSearchTool
    with pytest.raises(ValueError):
        registry.register(MockWebSearchTool())

@pytest.mark.asyncio
async def test_safe_executor_success():
    registry = ToolRegistry()
    tool = registry.get("web_search")
    
    result = await SafeExecutor.execute_tool(tool, {})
    assert result.success is True
    assert result.output.result == "Search results mock"
    assert result.duration >= 0

@pytest.mark.asyncio
async def test_safe_executor_validation_failure():
    registry = ToolRegistry()
    tool = registry.get("auth_recon")
    
    # Missing required 'target' field
    result = await SafeExecutor.execute_tool(tool, {}, auth_scope=AuthorizationScope(allowed_targets=["10.0.0.1"]))
    assert result.success is False
    assert "validation error" in result.error.lower() or "missing" in result.error.lower()

@pytest.mark.asyncio
async def test_safe_executor_authorization_failure():
    registry = ToolRegistry()
    tool = registry.get("auth_recon")
    
    # Missing auth scope entirely
    result = await SafeExecutor.execute_tool(tool, {"target": "10.0.0.1"})
    assert result.success is False
    assert "requires an authorizationscope" in result.error.lower()
    
    # Target not in auth scope
    scope = AuthorizationScope(allowed_targets=["192.168.1.1"])
    result = await SafeExecutor.execute_tool(tool, {"target": "10.0.0.1"}, auth_scope=scope)
    assert result.success is False
    assert "not in the authorized scope" in result.error.lower()

@pytest.mark.asyncio
async def test_safe_executor_timeout():
    registry = ToolRegistry()
    tool = registry.get("timeout_tool")
    
    result = await SafeExecutor.execute_tool(tool, {})
    assert result.success is False
    assert "timed out" in result.error.lower()


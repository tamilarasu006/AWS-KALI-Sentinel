import pytest
from unittest.mock import MagicMock

from OpenDEMON.kali.tools.calling import ToolCallParser, ToolCallValidator
from OpenDEMON.kali.tools.registry import ToolRegistry
from OpenDEMON.kali.tools.tool import KaliTool
from OpenDEMON.kali.permissions.risk import RiskLevel

@pytest.fixture
def registry():
    reg = ToolRegistry()
    
    class DummyTool(KaliTool):
        async def execute(self, arguments, context):
            return "ok"

    from pydantic import BaseModel
    class TestToolInput(BaseModel):
        target: str
        
    class TestToolOutput(BaseModel):
        result: str
        
    tool = DummyTool(
        name="test_tool",
        description="A test tool",
        category="general",
        risk_level=RiskLevel.LOW,
        required_capability="general",
        input_schema=TestToolInput,
        output_schema=TestToolOutput,
        enabled=True
    )
    reg.register(tool)
    return reg

def test_tool_call_parser_valid_json():
    raw_json = '```json\n{"call_id": "123", "tool_name": "test_tool", "arguments": {"target": "abc"}}\n```'
    call = ToolCallParser.parse(raw_json)
    assert call.call_id == "123"
    assert call.tool_name == "test_tool"
    assert call.arguments == {"target": "abc"}

def test_tool_call_parser_malformed():
    raw_json = '{"call_id": "123", "tool_name": "test_tool", "arguments": {"target": "abc"' # missing closing brace
    with pytest.raises(ValueError, match="Malformed JSON"):
        ToolCallParser.parse(raw_json)

def test_tool_call_validator_success(registry):
    validator = ToolCallValidator(registry)
    call = ToolCallParser.parse('{"call_id": "1", "tool_name": "test_tool", "arguments": {"target": "abc"}}')
    validator.validate(call)  # Should not raise

def test_tool_call_validator_unknown_tool(registry):
    validator = ToolCallValidator(registry)
    call = ToolCallParser.parse('{"call_id": "1", "tool_name": "hacker_tool", "arguments": {}}')
    with pytest.raises(ValueError, match="Unknown tool: 'hacker_tool' is not registered"):
        validator.validate(call)

def test_tool_call_validator_schema_violation(registry):
    validator = ToolCallValidator(registry)
    # Missing required 'target'
    call = ToolCallParser.parse('{"call_id": "1", "tool_name": "test_tool", "arguments": {}}')
    with pytest.raises(ValueError, match="Schema validation failed"):
        validator.validate(call)
        
def test_tool_call_validator_spoofing(registry):
    validator = ToolCallValidator(registry)
    call = ToolCallParser.parse('{"call_id": "1", "tool_name": "test_tool", "arguments": {"target": "abc", "risk_level": "LOW"}}')
    with pytest.raises(ValueError, match="Security violation: Spoofing protected field"):
        validator.validate(call)

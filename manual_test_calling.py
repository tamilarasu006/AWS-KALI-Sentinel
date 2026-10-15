import json
from unittest.mock import MagicMock
from OpenDEMON.kali.tools.calling import ToolCallParser, ToolCallValidator
from OpenDEMON.kali.tools.registry import ToolRegistry
from OpenDEMON.kali.tools.tool import KaliTool
from OpenDEMON.kali.permissions.risk import RiskLevel

def run():
    print("Testing Structured Tool Calling...")
    
    registry = ToolRegistry()
    class DummyTool(KaliTool):
        async def execute(self, arguments, context):
            return "ok"

    from pydantic import BaseModel
    class ReadFileInput(BaseModel):
        path: str
        
    class ReadFileOutput(BaseModel):
        content: str
        
    registry.register(DummyTool(
        name="read_file",
        description="Reads a file.",
        category="fs",
        risk_level=RiskLevel.MEDIUM,
        required_capability="fs_read",
        input_schema=ReadFileInput,
        output_schema=ReadFileOutput,
        enabled=True
    ))
    
    validator = ToolCallValidator(registry)
    
    print("\n--- Test 1: Successful Parse & Validate ---")
    raw = '```\n{"call_id": "abc-1", "tool_name": "read_file", "arguments": {"path": "/tmp/test.txt"}}\n```'
    call = ToolCallParser.parse(raw)
    validator.validate(call)
    print("Success: Call parsed and validated correctly.")
    
    print("\n--- Test 2: Unknown Tool Rejection ---")
    raw2 = '{"call_id": "2", "tool_name": "rm_rf", "arguments": {}}'
    call2 = ToolCallParser.parse(raw2)
    try:
        validator.validate(call2)
        assert False
    except ValueError as e:
        print(f"Caught correctly: {e}")
        
    print("\n--- Test 3: Schema Spoofing Rejection ---")
    raw3 = '{"call_id": "3", "tool_name": "read_file", "arguments": {"path": "/tmp/test.txt", "risk_level": "LOW"}}'
    call3 = ToolCallParser.parse(raw3)
    try:
        validator.validate(call3)
        assert False
    except ValueError as e:
        print(f"Caught correctly: {e}")
        
    print("\n--- Test 4: Schema Type Violation Rejection ---")
    raw4 = '{"call_id": "4", "tool_name": "read_file", "arguments": {"path": 123}}'
    call4 = ToolCallParser.parse(raw4)
    try:
        validator.validate(call4)
        assert False
    except ValueError as e:
        print(f"Caught correctly: {e}")
        
    print("\nALL TESTS PASSED MANUALLY!")

if __name__ == "__main__":
    run()

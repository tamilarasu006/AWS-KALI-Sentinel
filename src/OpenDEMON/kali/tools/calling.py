
import json
import jsonschema
from typing import Dict, Any, Optional
from pydantic import BaseModel
from OpenDEMON.kali.tools.registry import ToolRegistry

class ToolCall(BaseModel):
    type: str = "tool_call"
    tool: str
    arguments: Dict[str, Any]

class ToolResult(BaseModel):
    type: str = "tool_result"
    tool: str
    status: str
    result: Any

def normalize_tool_call(raw_text: str) -> str:
    text = raw_text.strip()
    if text.startswith("```json"): text = text[7:]
    elif text.startswith("```"): text = text[3:]
    if text.endswith("```"): text = text[:-3]
    return text.strip()

def parse_tool_call(raw_text: str) -> ToolCall:
    text = normalize_tool_call(raw_text)
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Malformed JSON: {str(e)}")
        
    if not isinstance(data, dict):
        raise ValueError("Tool call must be a JSON object.")
        
    if data.get("type") != "tool_call":
        raise ValueError("Tool call must have 'type': 'tool_call'.")
        
    if "tool" not in data or "arguments" not in data:
        raise ValueError("Tool call missing required fields (tool, arguments).")
        
    if not isinstance(data["arguments"], dict):
        raise ValueError("'arguments' must be a JSON object.")
        
    return ToolCall(
        tool=str(data["tool"]),
        arguments=data["arguments"]
    )

def validate_tool_arguments(tool_name: str, arguments: dict, registry: ToolRegistry):
    tool = registry.get(tool_name)
    if not tool:
        raise ValueError(f"Unknown tool: '{tool_name}' is not registered.")
    
    protected_keys = ["risk_level", "permissions", "capabilities"]
    for key in protected_keys:
        if key in arguments:
            raise ValueError(f"Security violation: Spoofing protected field '{key}'.")
            
    try:
        tool.validate_input(arguments)
    except Exception as e:
        raise ValueError(f"Schema validation failed for tool '{tool_name}': {str(e)}")

def validate_tool_call(call: ToolCall, registry: ToolRegistry) -> None:
    validate_tool_arguments(call.tool, call.arguments, registry)

def validate_tool_result(result: ToolResult) -> None:
    if result.type != "tool_result":
        raise ValueError("Invalid type.")
    if result.status not in ["success", "error", "timeout", "denied", "approval_required"]:
        raise ValueError("Invalid status.")

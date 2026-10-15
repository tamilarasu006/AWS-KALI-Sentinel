from typing import Dict, Any, Optional

class KALIRouter:
    """Routes requests and handles fallbacks for tools and models."""
    
    def __init__(self, primary_model: str = "kali-transformer"):
        self.primary_model = primary_model

    def route_model(self, failure_detected: bool = False) -> str:
        """Determines which model to use. Can fallback if the primary fails."""
        if failure_detected:
            return "fallback-heuristic-model"
        return self.primary_model

    def fallback_on_tool_failure(self, tool_name: str, error: str) -> str:
        """Generates a fallback prompt or context when a tool fails."""
        return f"[System Note: The tool '{tool_name}' failed with error: {error}. Please inform the user gracefully.]"

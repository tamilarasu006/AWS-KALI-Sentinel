from typing import List, Dict, Any
from OpenDEMON.kali.tokenizer.tokenizer import KALITokenizer

class KALIChatTemplate:
    """
    Canonical conversation format for KALI.
    """
    def __init__(self, tokenizer: KALITokenizer):
        self.tokenizer = tokenizer
        
    def format_messages(self, messages: List[Dict[str, str]]) -> str:
        """Formats a list of messages into a single string."""
        formatted = ""
        for msg in messages:
            role = msg["role"].upper()
            content = msg["content"]
            formatted += f"<{role}>\n{content}\n\n"
        return formatted
        
    def validate_messages(self, messages: List[Dict[str, str]]) -> bool:
        if not messages: return False
        valid_roles = {"system", "user", "assistant", "tool"}
        for msg in messages:
            if msg.get("role") not in valid_roles or not msg.get("content"):
                return False
        return True

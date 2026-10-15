"""Special tokens definition for KALI AI tokenizer."""

from dataclasses import dataclass
from typing import Optional

@dataclass
class SpecialTokens:
    """Container for tokenizer special tokens."""
    bos_token: str = "<bos>"
    eos_token: str = "<eos>"
    pad_token: str = "<pad>"
    unk_token: str = "<unk>"
    
    bos_token_id: Optional[int] = None
    eos_token_id: Optional[int] = None
    pad_token_id: Optional[int] = None
    unk_token_id: Optional[int] = None

    user_token: str = "<user>"
    assistant_token: str = "<assistant>"
    tool_token: str = "<tool>"
    
    user_token_id: Optional[int] = None
    assistant_token_id: Optional[int] = None
    tool_token_id: Optional[int] = None

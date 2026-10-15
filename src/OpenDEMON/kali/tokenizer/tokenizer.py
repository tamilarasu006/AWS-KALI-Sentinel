"""Tokenizer interface and concrete dummy fallback."""

from abc import ABC, abstractmethod
from typing import List, Union
from .special_tokens import SpecialTokens

class KALITokenizer(ABC):
    """Base interface for all KALI AI tokenizers."""
    
    def __init__(self, special_tokens: SpecialTokens):
        self.special_tokens = special_tokens

    @abstractmethod
    def encode(self, text: str, add_bos: bool = True) -> List[int]:
        """Encode a string into a list of token IDs."""
        pass

    @abstractmethod
    def decode(self, token_ids: List[int], skip_special_tokens: bool = True) -> str:
        """Decode a list of token IDs into a string."""
        pass

    def encode_batch(self, texts: List[str], add_bos: bool = True) -> List[List[int]]:
        """Encode a batch of strings."""
        return [self.encode(text, add_bos) for text in texts]

    def decode_batch(self, token_ids_batch: List[List[int]], skip_special_tokens: bool = True) -> List[str]:
        """Decode a batch of token IDs."""
        return [self.decode(token_ids, skip_special_tokens) for token_ids in token_ids_batch]

    @abstractmethod
    def token_to_id(self, token: str) -> int:
        """Convert a single token string to its ID."""
        pass

    @abstractmethod
    def id_to_token(self, token_id: int) -> str:
        """Convert a single token ID to its string representation."""
        pass

    @abstractmethod
    def vocab_size(self) -> int:
        """Return the size of the vocabulary."""
        pass


class DummyKALITokenizer(KALITokenizer):
    """A simplistic character-level tokenizer for proving the inference pipeline without external models."""
    
    def __init__(self, vocab_size: int = 32000):
        # We place special tokens at the beginning of the vocab
        special = SpecialTokens(
            bos_token="<bos>",
            eos_token="<eos>",
            pad_token="<pad>",
            unk_token="<unk>",
            bos_token_id=0,
            eos_token_id=1,
            pad_token_id=2,
            unk_token_id=3,
        )
        super().__init__(special)
        self._vocab_size = vocab_size

    def encode(self, text: str, add_bos: bool = True) -> List[int]:
        tokens = []
        if add_bos and self.special_tokens.bos_token_id is not None:
            tokens.append(self.special_tokens.bos_token_id)
            
        for c in text:
            # Shift characters so they don't collide with the 4 special tokens
            # We map ascii 0-255 to 4-259
            tid = ord(c) + 4
            if tid >= self._vocab_size:
                tid = self.special_tokens.unk_token_id
            tokens.append(tid)
            
        return tokens

    def decode(self, token_ids: List[int], skip_special_tokens: bool = True) -> str:
        chars = []
        special_ids = {
            self.special_tokens.bos_token_id,
            self.special_tokens.eos_token_id,
            self.special_tokens.pad_token_id,
            self.special_tokens.unk_token_id
        }
        
        for tid in token_ids:
            if tid in special_ids:
                if not skip_special_tokens:
                    if tid == self.special_tokens.bos_token_id:
                        chars.append(self.special_tokens.bos_token)
                    elif tid == self.special_tokens.eos_token_id:
                        chars.append(self.special_tokens.eos_token)
                    elif tid == self.special_tokens.pad_token_id:
                        chars.append(self.special_tokens.pad_token)
                    elif tid == self.special_tokens.unk_token_id:
                        chars.append(self.special_tokens.unk_token)
                continue
                
            # Shift back
            char_code = tid - 4
            if 0 <= char_code <= 0x10FFFF: # valid unicode range
                try:
                    chars.append(chr(char_code))
                except ValueError:
                    chars.append("?")
            else:
                chars.append("?")
                
        return "".join(chars)

    def token_to_id(self, token: str) -> int:
        if token == self.special_tokens.bos_token:
            return self.special_tokens.bos_token_id
        elif token == self.special_tokens.eos_token:
            return self.special_tokens.eos_token_id
        elif token == self.special_tokens.pad_token:
            return self.special_tokens.pad_token_id
        elif token == self.special_tokens.unk_token:
            return self.special_tokens.unk_token_id
            
        if len(token) == 1:
            return min(ord(token) + 4, self._vocab_size - 1)
        return self.special_tokens.unk_token_id

    def id_to_token(self, token_id: int) -> str:
        if token_id == self.special_tokens.bos_token_id:
            return self.special_tokens.bos_token
        elif token_id == self.special_tokens.eos_token_id:
            return self.special_tokens.eos_token
        elif token_id == self.special_tokens.pad_token_id:
            return self.special_tokens.pad_token
        elif token_id == self.special_tokens.unk_token_id:
            return self.special_tokens.unk_token
            
        char_code = token_id - 4
        if 0 <= char_code <= 0x10FFFF:
            try:
                return chr(char_code)
            except ValueError:
                return "<unk>"
        return "<unk>"

    def vocab_size(self) -> int:
        return self._vocab_size

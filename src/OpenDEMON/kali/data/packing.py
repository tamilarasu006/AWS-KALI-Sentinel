from typing import List, Iterator

class DocumentPacker:
    """
    Packs multiple short documents into chunks of max_seq_length.
    """
    def __init__(self, max_seq_length: int, eos_token_id: int):
        self.max_seq_length = max_seq_length
        self.eos_token_id = eos_token_id
        self._buffer: List[int] = []

    def add_tokens(self, tokens: List[int]) -> Iterator[List[int]]:
        self._buffer.extend(tokens)
        self._buffer.append(self.eos_token_id)
        
        while len(self._buffer) >= self.max_seq_length:
            yield self._buffer[:self.max_seq_length]
            self._buffer = self._buffer[self.max_seq_length:]

    def flush(self) -> List[int]:
        res = self._buffer.copy()
        self._buffer.clear()
        return res

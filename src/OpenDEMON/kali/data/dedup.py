import hashlib
from typing import Set

class Deduplicator:
    """
    Implements exact deduplication based on content hashes.
    """
    def __init__(self):
        self.seen_hashes: Set[str] = set()

    def _hash(self, text: str) -> str:
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    def is_duplicate(self, text: str) -> bool:
        h = self._hash(text)
        if h in self.seen_hashes:
            return True
        self.seen_hashes.add(h)
        return False

    def reset(self):
        self.seen_hashes.clear()

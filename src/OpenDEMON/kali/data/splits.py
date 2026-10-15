import random
from typing import List, Tuple, Any

class DatasetSplitter:
    """
    Creates deterministic train, validation, and test splits.
    """
    def __init__(self, train_pct: float = 0.8, val_pct: float = 0.1, test_pct: float = 0.1, seed: int = 42):
        self.train_pct = train_pct
        self.val_pct = val_pct
        self.test_pct = test_pct
        self.seed = seed
        random.seed(self.seed)

    def split(self, data: List[Any]) -> Tuple[List[Any], List[Any], List[Any]]:
        shuffled_data = data.copy()
        random.shuffle(shuffled_data)
        n = len(shuffled_data)
        train_end = int(n * self.train_pct)
        val_end = train_end + int(n * self.val_pct)
        return shuffled_data[:train_end], shuffled_data[train_end:val_end], shuffled_data[val_end:]

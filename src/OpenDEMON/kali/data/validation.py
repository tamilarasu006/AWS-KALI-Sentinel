class ContextValidator:
    def __init__(self, max_context_length: int, strategy: str = "truncate"):
        self.max_context_length = max_context_length
        self.strategy = strategy
        self.stats = {"truncated": 0, "rejected": 0, "split": 0}
        
    def validate(self, tokens: list) -> list:
        if len(tokens) <= self.max_context_length:
            return [tokens]
            
        if self.strategy == "truncate":
            self.stats["truncated"] += 1
            return [tokens[:self.max_context_length]]
        elif self.strategy == "reject":
            self.stats["rejected"] += 1
            return []
        elif self.strategy == "split":
            self.stats["split"] += 1
            return [tokens[i:i+self.max_context_length] for i in range(0, len(tokens), self.max_context_length)]
        return [tokens]

from typing import List
from OpenDEMON.database.models.document import DocumentChunk

class ContextBuilder:
    """Builds an LLM prompt context from retrieved chunks."""

    @classmethod
    def build(cls, chunks: List[DocumentChunk], max_tokens: int = 4000) -> str:
        """
        Formats chunks into a context string.
        Truncates if it exceeds a rough token limit.
        """
        if not chunks:
            return ""

        context_parts = []
        current_len = 0

        for i, chunk in enumerate(chunks):
            # Using simple whitespace splitting as proxy for token count
            chunk_len = len(chunk.content.split())
            if current_len + chunk_len > max_tokens:
                break
            
            part = f"--- Document Context {i+1} ---\n{chunk.content}\n"
            context_parts.append(part)
            current_len += chunk_len

        return "\n".join(context_parts)

from abc import ABC, abstractmethod
from typing import List
from OpenDEMON.database.models.document import DocumentChunk

class DocumentReranker(ABC):
    """Abstract interface for reranking document chunks."""

    @abstractmethod
    def rerank(self, query: str, chunks: List[DocumentChunk], top_k: int) -> List[DocumentChunk]:
        """Reranks the retrieved chunks based on the original query."""
        pass

class IdentityReranker(DocumentReranker):
    """A passthrough reranker that simply truncates to top_k."""

    def rerank(self, query: str, chunks: List[DocumentChunk], top_k: int) -> List[DocumentChunk]:
        return chunks[:top_k]

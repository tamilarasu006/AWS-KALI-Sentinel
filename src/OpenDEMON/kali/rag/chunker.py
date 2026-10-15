from dataclasses import dataclass, field
from typing import Dict, Any, List

@dataclass
class ChunkConfig:
    chunk_size: int = 512
    chunk_overlap: int = 64
    min_chunk_size: int = 50

@dataclass
class Chunk:
    content: str
    document_id: str
    source: str
    chunk_index: int
    metadata: Dict[str, Any] = field(default_factory=dict)

class DocumentChunker:
    """Chunks cleaned text into overlapping segments."""

    def __init__(self, config: ChunkConfig = None):
        self.config = config or ChunkConfig()

    def _count_tokens(self, text: str) -> int:
        return len(text.split())

    def chunk(self, text: str, document_id: str, source: str = "", metadata: Dict[str, Any] = None) -> List[Chunk]:
        """
        Splits text into chunks respecting the chunk_size and chunk_overlap.
        """
        if not text or not text.strip():
            return []

        base_meta = metadata or {}
        
        # Simple paragraph splitting
        paragraphs = [p for p in text.split("\n\n") if p.strip()]

        chunks: List[Chunk] = []
        current_tokens: List[str] = []

        for para in paragraphs:
            para_tokens = para.split()
            
            if current_tokens and len(current_tokens) + len(para_tokens) > self.config.chunk_size:
                chunk_content = " ".join(current_tokens)
                if self._count_tokens(chunk_content) >= self.config.min_chunk_size:
                    chunks.append(
                        Chunk(
                            content=chunk_content,
                            document_id=document_id,
                            source=source,
                            chunk_index=len(chunks),
                            metadata=base_meta.copy()
                        )
                    )
                
                # Overlap
                if self.config.chunk_overlap > 0 and len(current_tokens) > self.config.chunk_overlap:
                    current_tokens = current_tokens[-self.config.chunk_overlap:]
                else:
                    current_tokens = []
            
            # If a single paragraph is larger than chunk_size
            if len(para_tokens) > self.config.chunk_size:
                if current_tokens:
                    chunk_content = " ".join(current_tokens)
                    if self._count_tokens(chunk_content) >= self.config.min_chunk_size:
                        chunks.append(
                            Chunk(
                                content=chunk_content,
                                document_id=document_id,
                                source=source,
                                chunk_index=len(chunks),
                                metadata=base_meta.copy()
                            )
                        )
                    current_tokens = []
                
                idx = 0
                while idx < len(para_tokens):
                    window = para_tokens[idx : idx + self.config.chunk_size]
                    chunk_content = " ".join(window)
                    if self._count_tokens(chunk_content) >= self.config.min_chunk_size:
                        chunks.append(
                            Chunk(
                                content=chunk_content,
                                document_id=document_id,
                                source=source,
                                chunk_index=len(chunks),
                                metadata=base_meta.copy()
                            )
                        )
                    step = max(1, self.config.chunk_size - self.config.chunk_overlap)
                    idx += step
                continue
            
            current_tokens.extend(para_tokens)

        # Flush remaining
        if current_tokens:
            chunk_content = " ".join(current_tokens)
            if not chunks or self._count_tokens(chunk_content) >= self.config.min_chunk_size:
                chunks.append(
                    Chunk(
                        content=chunk_content,
                        document_id=document_id,
                        source=source,
                        chunk_index=len(chunks),
                        metadata=base_meta.copy()
                    )
                )

        return chunks

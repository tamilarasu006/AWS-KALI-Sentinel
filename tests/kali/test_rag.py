import pytest
import os
import tempfile
from pathlib import Path
from OpenDEMON.kali.rag import (
    DocumentLoader,
    DocumentParser,
    DocumentChunker,
    ChunkConfig,
    FakeEmbeddingProvider,
    ContextBuilder,
    RAGPipeline
)

def test_document_loader():
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
        f.write(b"Hello KALI")
        temp_path = f.name
    
    try:
        content = DocumentLoader.load(temp_path)
        assert content == "Hello KALI"
    finally:
        os.remove(temp_path)

def test_document_parser():
    raw = "This    is   some \n\n\n raw text.  "
    cleaned, meta = DocumentParser.parse(raw, source="test.txt")
    assert cleaned == "This    is   some\n\nraw text."
    assert meta["source"] == "test.txt"

def test_document_chunker():
    config = ChunkConfig(chunk_size=10, chunk_overlap=2, min_chunk_size=1)
    chunker = DocumentChunker(config)
    
    text = "word " * 25
    chunks = chunker.chunk(text, document_id="doc1", source="test")
    
    assert len(chunks) > 1
    assert chunks[0].document_id == "doc1"
    assert "word" in chunks[0].content

def test_fake_embeddings():
    provider = FakeEmbeddingProvider(dimension=10)
    emb = provider.embed("test")
    assert len(emb) == 10
    
    batch = provider.embed_batch(["one", "two"])
    assert len(batch) == 2
    assert len(batch[0]) == 10

def test_context_builder():
    from OpenDEMON.database.models.document import DocumentChunk
    
    chunks = [
        DocumentChunk(content="First piece of context"),
        DocumentChunk(content="Second piece of context")
    ]
    
    context = ContextBuilder.build(chunks)
    assert "First piece of context" in context
    assert "Second piece of context" in context
    assert "Document Context 1" in context
    assert "Document Context 2" in context

@pytest.mark.asyncio
async def test_rag_pipeline_augmentation():
    # Test just the augmentation part without DB
    provider = FakeEmbeddingProvider()
    pipeline = RAGPipeline(retriever=None, embedding_provider=provider)
    
    prompt = "What is KALI?"
    context = "KALI is an AI framework."
    
    augmented = pipeline.augment_prompt(prompt, context)
    assert "What is KALI?" in augmented
    assert "KALI is an AI framework." in augmented

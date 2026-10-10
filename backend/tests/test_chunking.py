import pytest
from app.pipeline.chunking.sentence_window import split_into_sentences, chunk_document

def test_split_sentences_basic():
    text = "This is a sentence. This is another one. And a third."
    sentences = split_into_sentences(text)
    assert len(sentences) >= 2

def test_chunk_document_returns_chunks():
    text = (
        "The Contractor shall indemnify the Client against all losses. "
        "This Agreement shall be governed by English law. "
        "Either party may terminate this agreement with 30 days notice. "
        "The Client shall pay the Contractor within 30 days of invoice. "
        "Neither party shall be liable for consequential damages."
    )
    chunks = chunk_document(text, window_size=3, overlap=1)
    assert len(chunks) > 0
    for chunk in chunks:
        assert chunk.text
        assert chunk.id

def test_chunk_empty_text():
    chunks = chunk_document("", window_size=3, overlap=1)
    assert chunks == []

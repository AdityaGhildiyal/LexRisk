import pytest
from app.pipeline.chunking.sentence_window import chunk_document, strip_page_headers_and_footers

def test_strip_page_headers_and_footers():
    pages = [
        "Confidential Agreement\nSection 1.1 First clause.\nSection 1.2 Detail.\nPage 1 of 2",
        "Confidential Agreement\nSection 2.1 Second clause.\nSection 2.2 More text.\nPage 2 of 2"
    ]
    cleaned = strip_page_headers_and_footers(pages)
    assert len(cleaned) == 2
    assert "Section 1.1 First clause." in cleaned[0]
    assert "Section 2.1 Second clause." in cleaned[1]

def test_chunk_document_returns_chunks():
    text = (
        "1.1 Indemnity. The Contractor shall indemnify the Client against all losses.\n\n"
        "2.1 Governing Law. This Agreement shall be governed by English law.\n\n"
        "3.1 Termination. Either party may terminate this agreement with 30 days notice.\n\n"
        "4.1 Payment. The Client shall pay the Contractor within 30 days of invoice.\n\n"
        "5.1 Limitation of Liability. Neither party shall be liable for consequential damages."
    )
    chunks = chunk_document(text)
    assert len(chunks) > 0
    for chunk in chunks:
        assert chunk.text
        assert chunk.id

def test_chunk_empty_text():
    chunks = chunk_document("")
    assert chunks == []

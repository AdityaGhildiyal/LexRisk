import pytest
from unittest.mock import AsyncMock, patch
from app.models.clause import Chunk
from app.pipeline.extraction.llm_extractor import LLMExtractor, KNOWN_CLAUSE_TYPES

@pytest.mark.asyncio
async def test_extractor_returns_clauses():
    chunk = Chunk(
        id="test-chunk-1",
        text="The Contractor shall indemnify the Client against all losses arising from negligence.",
        char_start=0, char_end=80
    )
    
    mock_response = [{
        "clause_type": "indemnity",
        "span": "The Contractor shall indemnify the Client against all losses arising from negligence.",
        "confidence": 0.95
    }]
    
    with patch("app.pipeline.extraction.llm_extractor.extract_clauses_from_text", 
               new=AsyncMock(return_value=mock_response)):
        extractor = LLMExtractor(cache=None)
        clauses = await extractor.extract([chunk])
        
        assert len(clauses) == 1
        assert clauses[0].clause_type == "indemnity"
        assert clauses[0].confidence == 0.95

@pytest.mark.asyncio
async def test_extractor_normalizes_unknown_type():
    chunk = Chunk(
        id="test-2",
        text="The Provider shall provide notice 30 days prior to changing terms.",
        char_start=0,
        char_end=66
    )
    
    mock_response = [{
        "clause_type": "unknown_random_type",
        "span": "The Provider shall provide notice 30 days prior to changing terms.",
        "confidence": 0.5
    }]
    
    with patch("app.pipeline.extraction.llm_extractor.extract_clauses_from_text",
               new=AsyncMock(return_value=mock_response)):
        extractor = LLMExtractor(cache=None)
        clauses = await extractor.extract([chunk])
        assert len(clauses) == 1
        assert clauses[0].clause_type == "other"

import pytest
from unittest.mock import AsyncMock, patch
from app.models.clause import Clause
from app.pipeline.summarization.summarizer import ClauseSummarizer

@pytest.mark.asyncio
async def test_summarizer_returns_summary():
    clause = Clause(
        id="clause-1",
        chunk_id="chunk-1",
        text="The Contractor shall indemnify the Client.",
        clause_type="indemnity"
    )
    
    mock_raw = {
        "meaning": "The contractor must cover the client's losses",
        "obligor": "Contractor",
        "trigger": "Any losses incurred by the Client",
        "consequence": "Contractor pays for losses"
    }
    
    with patch("app.pipeline.summarization.summarizer.summarize_clause",
               new=AsyncMock(return_value=mock_raw)):
        summarizer = ClauseSummarizer(cache=None)
        summary = await summarizer.summarize(clause)
        
        assert summary.clause_id == "clause-1"
        assert summary.meaning == mock_raw["meaning"]
        assert summary.faithfulness_score == 1.0  # no checker
        assert summary.faithfulness_flag == False

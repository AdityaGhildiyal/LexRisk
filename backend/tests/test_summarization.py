import pytest
from unittest.mock import AsyncMock, patch
from app.models.clause import Clause
from app.pipeline.summarization.summarizer import ClauseSummarizer

@pytest.mark.asyncio
async def test_summarizer_returns_summary():
    mock_raw = {
        "meaning": "The contractor must cover the client's losses",
        "obligor": "Contractor",
        "trigger": "Any losses incurred by the Client",
        "consequence": "Contractor pays for losses"
    }

    clause = Clause(
        id="clause-1",
        chunk_id="chunk-1",
        text="The Contractor shall indemnify the Client against all losses.",
        clause_type="indemnity",
        pre_summary=mock_raw
    )
    
    summarizer = ClauseSummarizer(cache=None)
    summary = await summarizer.summarize(clause)
    
    assert summary.clause_id == "clause-1"
    assert summary.meaning == mock_raw["meaning"]
    assert summary.faithfulness_score == 1.0  # no checker
    assert summary.faithfulness_flag == False

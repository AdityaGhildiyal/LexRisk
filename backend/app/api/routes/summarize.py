from fastapi import APIRouter, Request
from pydantic import BaseModel
from app.models.clause import Clause, ClauseSummary
from app.pipeline.summarization.summarizer import ClauseSummarizer
from app.pipeline.summarization.faithfulness import FaithfulnessChecker
from typing import List

router = APIRouter()
_faithfulness_checker = FaithfulnessChecker()

class SummarizeRequest(BaseModel):
    clauses: List[Clause]

@router.post("/summarize", response_model=List[ClauseSummary])
async def summarize_clauses(request: Request, body: SummarizeRequest):
    """Stage endpoint: summarize extracted clauses with faithfulness checking."""
    cache = getattr(request.app.state, "cache", None)
    summarizer = ClauseSummarizer(cache=cache)
    summaries = []
    for clause in body.clauses:
        summary = await summarizer.summarize(clause, faithfulness_checker=_faithfulness_checker)
        summaries.append(summary)
    return summaries

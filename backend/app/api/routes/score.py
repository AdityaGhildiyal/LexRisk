from fastapi import APIRouter
from pydantic import BaseModel
from app.models.clause import Clause, DeviationResult, RiskScore
from app.pipeline.risk.scorer import score_clause
from typing import List

router = APIRouter()

class ScoreRequest(BaseModel):
    clauses: List[Clause]
    deviation_results: List[DeviationResult]

@router.post("/score", response_model=List[RiskScore])
async def score_clauses(body: ScoreRequest):
    """Stage endpoint: compute risk scores from clauses and deviation results."""
    deviation_map = {d.clause_id: d for d in body.deviation_results}
    scores = []
    for clause in body.clauses:
        deviation = deviation_map.get(clause.id, DeviationResult(
            clause_id=clause.id, deviation_score=0.5, percentile=50.0
        ))
        scores.append(score_clause(clause, deviation))
    return scores

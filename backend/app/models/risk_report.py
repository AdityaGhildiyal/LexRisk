from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid

class ClauseReport(BaseModel):
    clause_id: str
    clause_type: str
    text: str
    section: Optional[str] = None
    summary: dict  # ClauseSummary as dict
    deviation_score: Optional[float] = None
    risk_score: float
    risk_rationale: str

class RiskReport(BaseModel):
    contract_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    generated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    clauses: List[ClauseReport]
    total_clauses: int
    high_risk_count: int
    faithfulness_flags: int

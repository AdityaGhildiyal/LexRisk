from pydantic import BaseModel, Field
from typing import Optional, List
import uuid

class Chunk(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text: str
    section_heading: Optional[str] = None
    page_number: Optional[int] = None
    char_start: int = 0
    char_end: int = 0

class Clause(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    chunk_id: str
    text: str
    clause_type: str
    span: Optional[str] = None
    confidence: float = 1.0
    section: Optional[str] = None
    pre_summary: Optional[dict] = None

class ClauseSummary(BaseModel):
    clause_id: str
    meaning: str
    obligor: str
    trigger: str
    consequence: str
    faithfulness_score: float
    faithfulness_flag: bool

class DeviationResult(BaseModel):
    clause_id: str
    deviation_score: Optional[float] = None
    percentile: Optional[float] = None
    is_computed: bool = False
    nearest_neighbor_ids: List[str] = []

class RiskScore(BaseModel):
    clause_id: str
    risk_score: float
    clause_type_weight: float
    rationale: str

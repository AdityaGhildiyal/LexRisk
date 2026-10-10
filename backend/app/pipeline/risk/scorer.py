"""
Interpretable risk scorer.
Formula:
- When FAISS reference corpus index is loaded:
    risk_score = 0.6 * normalized_deviation + 0.4 * clause_type_weight
- When FAISS reference corpus index is not built yet (Phase 3 pending):
    risk_score = 1.0 * clause_type_weight (deviation is NOT faked or claimed).
"""
import logging
from app.models.clause import Clause, DeviationResult, RiskScore
from app.core.config import settings

logger = logging.getLogger(__name__)

DEVIATION_WEIGHT = 0.6
CLAUSE_TYPE_WEIGHT = 0.4

RISK_LABELS = {
    (0.0, 0.35): "Low Risk",
    (0.35, 0.65): "Moderate Risk",
    (0.65, 0.80): "High Risk",
    (0.80, 1.01): "Critical Risk",
}

def get_risk_label(score: float) -> str:
    for (low, high), label in RISK_LABELS.items():
        if low <= score < high:
            return label
    return "Moderate Risk"

def score_clause(clause: Clause, deviation_result: DeviationResult) -> RiskScore:
    """
    Compute risk score for a clause.
    Transparently marks if deviation was computed vs uncomputed.
    """
    type_weight = settings.clause_type_weights.get(
        clause.clause_type, 
        settings.clause_type_weights.get("other", 0.5)
    )

    is_computed = getattr(deviation_result, "is_computed", False)

    if is_computed and deviation_result.deviation_score is not None:
        deviation = max(0.0, min(1.0, deviation_result.deviation_score))
        risk_score = DEVIATION_WEIGHT * deviation + CLAUSE_TYPE_WEIGHT * type_weight
        risk_score = max(0.0, min(1.0, risk_score))
        label = get_risk_label(risk_score)
        
        rationale = (
            f"{label}. "
            f"Clause type '{clause.clause_type}' assigned base critical weight of {type_weight:.2f}. "
            f"Empirical corpus anomaly: {deviation:.2f} ({deviation_result.percentile:.0f}th percentile). "
            f"Scoring: {DEVIATION_WEIGHT}×{deviation:.2f} + {CLAUSE_TYPE_WEIGHT}×{type_weight:.2f} = {risk_score:.2f}."
        )
    else:
        # Reference corpus not indexed yet — do NOT fabricate a 50% percentile
        risk_score = type_weight
        label = get_risk_label(risk_score)
        
        rationale = (
            f"{label}. "
            f"Clause type '{clause.clause_type}' carries a critical weight of {type_weight:.2f}. "
            f"Semantic anomaly: uncomputed (reference corpus index pending in Phase 3). "
            f"Risk rank currently derived directly from clause type criticality."
        )

    return RiskScore(
        clause_id=clause.id,
        risk_score=risk_score,
        clause_type_weight=type_weight,
        rationale=rationale,
    )

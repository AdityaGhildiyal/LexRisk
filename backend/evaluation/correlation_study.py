"""
Correlation study: Spearman's rho between system risk ranking and expert labels.

This is the headline metric of the research contribution.
See Phase 5 in the roadmap for full protocol details.

Usage:
    python evaluation/correlation_study.py \
        --expert-labels-path /data/expert_labels.json \
        --system-scores-path /data/system_scores.json \
        --output results/correlation.json

Expert labels format:
    [{
        "clause_id": "...",
        "clause_text": "...",
        "clause_type": "...",
        "expert_unusual_score": 0 or 1  (0=normal, 1=unusual)
    }]

System scores format (output of pipeline):
    [{
        "clause_id": "...",
        "risk_score": 0.0-1.0
    }]
"""
import argparse
import json
import logging
from typing import List, Dict, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def spearman_rho(x: List[float], y: List[float]) -> float:
    """Compute Spearman's rank correlation coefficient."""
    n = len(x)
    if n != len(y) or n < 2:
        raise ValueError(f"Incompatible or too-short lists: {len(x)}, {len(y)}")
    
    # Compute ranks
    def rank_list(lst):
        sorted_with_idx = sorted(enumerate(lst), key=lambda t: t[1])
        ranks = [0] * len(lst)
        for rank, (idx, _) in enumerate(sorted_with_idx, 1):
            ranks[idx] = rank
        return ranks
    
    rx = rank_list(x)
    ry = rank_list(y)
    
    d_sq_sum = sum((a - b) ** 2 for a, b in zip(rx, ry))
    rho = 1 - (6 * d_sq_sum) / (n * (n ** 2 - 1))
    return rho


def p_value_approx(rho: float, n: int) -> float:
    """Approximate p-value for Spearman's rho using t-distribution."""
    import math
    if abs(rho) == 1.0:
        return 0.0
    t = rho * math.sqrt((n - 2) / (1 - rho ** 2))
    # Rough approximation using normal distribution
    # For a proper p-value, use scipy.stats.spearmanr in practice
    from math import erfc, sqrt
    p = erfc(abs(t) / sqrt(2))
    return p


def run_correlation_study(
    expert_labels: List[Dict],
    system_scores: List[Dict]
) -> Dict:
    """
    Compute Spearman's rho between system risk scores and expert unusual labels.
    
    Args:
        expert_labels: List of {clause_id, expert_unusual_score} dicts
        system_scores: List of {clause_id, risk_score} dicts
    
    Returns:
        Dict with rho, p_value, n, interpretation
    """
    # Align on shared clause IDs
    expert_map = {e["clause_id"]: e["expert_unusual_score"] for e in expert_labels}
    system_map = {s["clause_id"]: s["risk_score"] for s in system_scores}
    shared_ids = [cid for cid in expert_map if cid in system_map]
    
    if len(shared_ids) < 10:
        raise ValueError(f"Too few shared clause IDs for correlation: {len(shared_ids)}")
    
    expert_scores = [expert_map[cid] for cid in shared_ids]
    sys_scores = [system_map[cid] for cid in shared_ids]
    
    rho = spearman_rho(sys_scores, expert_scores)
    p = p_value_approx(rho, len(shared_ids))
    
    # Interpret
    if rho >= 0.5:
        interpretation = "Strong positive correlation — system ranking aligns well with expert judgment"
    elif rho >= 0.3:
        interpretation = "Moderate positive correlation — system ranking partially aligns with expert judgment"
    elif rho >= 0.1:
        interpretation = "Weak positive correlation"
    elif rho < 0:
        interpretation = "Negative correlation — system and expert rankings disagree"
    else:
        interpretation = "No meaningful correlation"
    
    return {
        "n_clauses": len(shared_ids),
        "n_expert_labels": len(expert_labels),
        "n_system_scored": len(system_scores),
        "spearman_rho": round(rho, 4),
        "p_value_approx": round(p, 4),
        "significant_at_0_05": p < 0.05,
        "interpretation": interpretation,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LexRisk correlation study: Spearman rho")
    parser.add_argument("--expert-labels-path", required=True)
    parser.add_argument("--system-scores-path", required=True)
    parser.add_argument("--output", default="results/correlation.json")
    args = parser.parse_args()
    
    with open(args.expert_labels_path) as f:
        expert_labels = json.load(f)
    with open(args.system_scores_path) as f:
        system_scores = json.load(f)
    
    results = run_correlation_study(expert_labels, system_scores)
    
    import os
    os.makedirs(os.path.dirname(args.output) if os.path.dirname(args.output) else ".", exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"=== Correlation Study Results ===")
    logger.info(f"N clauses: {results['n_clauses']}")
    logger.info(f"Spearman's rho: {results['spearman_rho']:.4f}")
    logger.info(f"p-value (approx): {results['p_value_approx']:.4f} {'*' if results['significant_at_0_05'] else ''}")
    logger.info(f"Interpretation: {results['interpretation']}")
    logger.info(f"Results saved to {args.output}")

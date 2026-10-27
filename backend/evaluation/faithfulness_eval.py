"""
Faithfulness pass rate evaluation.

Usage:
    python evaluation/faithfulness_eval.py \
        --clauses-path /data/clauses.json \
        --output results/faithfulness.json

Runs the NLI faithfulness checker over a set of (clause, summary) pairs
and reports the pass rate and score distribution.
"""
import argparse
import asyncio
import json
import logging
from typing import List, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def evaluate_faithfulness(pairs: List[Dict], threshold: float = 0.5) -> Dict:
    """
    Evaluate faithfulness pass rate over (clause, summary) pairs.
    
    Args:
        pairs: List of {clause_text, summary_text} dicts
        threshold: NLI entailment score threshold for passing
    
    Returns:
        Dict with pass_rate, mean_score, score_distribution
    """
    from app.pipeline.summarization.faithfulness import FaithfulnessChecker
    
    checker = FaithfulnessChecker(threshold=threshold)
    scores = []
    passes = []
    
    for i, pair in enumerate(pairs):
        entailment_prob, is_flagged = await checker.check(
            premise=pair["clause_text"],
            hypothesis=pair["summary_text"]
        )
        scores.append(entailment_prob)
        if not is_flagged:
            passes.append(entailment_prob)
        if (i + 1) % 10 == 0:
            logger.info(f"Processed {i+1}/{len(pairs)} pairs")
    
    return {
        "total_pairs": len(scores),
        "pass_count": len(passes),
        "pass_rate": len(passes) / len(scores) if scores else 0.0,
        "mean_score": sum(scores) / len(scores) if scores else 0.0,
        "min_score": min(scores) if scores else 0.0,
        "max_score": max(scores) if scores else 0.0,
        "threshold": threshold,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LexRisk faithfulness pass rate evaluation")
    parser.add_argument("--clauses-path", required=True, help="Path to JSON with clause/summary pairs")
    parser.add_argument("--output", default="results/faithfulness.json")
    parser.add_argument("--threshold", type=float, default=0.5)
    args = parser.parse_args()
    
    logger.info("Loading clause/summary pairs...")
    with open(args.clauses_path) as f:
        pairs = json.load(f)
    
    results = asyncio.run(evaluate_faithfulness(pairs, args.threshold))
    
    import os
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Faithfulness pass rate: {results['pass_rate']:.1%} ({results['pass_count']}/{results['total_pairs']})")
    logger.info(f"Mean score: {results['mean_score']:.3f}")
    logger.info(f"Results saved to {args.output}")

"""
Extraction F1 evaluation against CUAD held-out labels.

Usage:
    python evaluation/extraction_f1.py \
        --cuad-test-path /data/cuad/test.json \
        --output results/extraction_f1.json

Computes per-clause-type precision, recall, and F1 for the LLM extractor
against CUAD's expert-labeled test set.
"""
import argparse
import json
import logging
from collections import defaultdict
from typing import Dict, List, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def compute_token_f1(prediction: str, ground_truth: str) -> Tuple[float, float, float]:
    """Compute token-level precision, recall, F1 between two strings."""
    pred_tokens = set(prediction.lower().split())
    gold_tokens = set(ground_truth.lower().split())
    
    if not pred_tokens and not gold_tokens:
        return 1.0, 1.0, 1.0
    if not pred_tokens or not gold_tokens:
        return 0.0, 0.0, 0.0
    
    common = pred_tokens & gold_tokens
    precision = len(common) / len(pred_tokens)
    recall = len(common) / len(gold_tokens)
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    return precision, recall, f1


def evaluate_extraction(predictions: List[Dict], ground_truths: List[Dict]) -> Dict:
    """
    Compute extraction F1 per clause type.
    
    Args:
        predictions: List of {clause_type, text} dicts from the extractor
        ground_truths: List of {clause_type, text} dicts from CUAD labels
    
    Returns:
        Dict with per-type and macro-averaged F1 scores
    """
    type_scores = defaultdict(list)
    
    for gt in ground_truths:
        clause_type = gt["clause_type"]
        best_f1 = 0.0
        for pred in predictions:
            if pred["clause_type"] == clause_type:
                _, _, f1 = compute_token_f1(pred["text"], gt["text"])
                best_f1 = max(best_f1, f1)
        type_scores[clause_type].append(best_f1)
    
    results = {}
    for clause_type, scores in type_scores.items():
        results[clause_type] = {
            "f1": sum(scores) / len(scores),
            "count": len(scores),
        }
    
    macro_f1 = sum(v["f1"] for v in results.values()) / len(results) if results else 0.0
    results["macro_f1"] = macro_f1
    
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LexRisk extraction F1 evaluation")
    parser.add_argument("--cuad-test-path", required=True)
    parser.add_argument("--output", default="results/extraction_f1.json")
    args = parser.parse_args()
    
    # Load CUAD test set and run evaluation
    logger.info("Extraction F1 evaluation — implementation pending Phase 5")
    logger.info(f"CUAD test path: {args.cuad_test_path}")
    logger.info(f"Output: {args.output}")

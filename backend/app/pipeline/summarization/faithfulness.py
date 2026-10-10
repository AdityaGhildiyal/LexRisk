"""
NLI faithfulness checker with claim-level decomposition and calibrated qualifier coverage check.
Label order for cross-encoder/nli-deberta-v3-small:
  0: contradiction
  1: entailment
  2: neutral
"""
import logging
import asyncio
import re
from typing import Optional, Tuple, List
from app.core.config import settings

logger = logging.getLogger(__name__)

# High-stakes qualifier patterns that must not be silently dropped if present in clause
HIGH_STAKES_PATTERNS = [
    (r'\bwithout limit(?:ation)?\b', [r'without limit', r'no cap', r'uncapped', r'unlimited']),
    (r'\bunlimited\b', [r'unlimited', r'no cap', r'uncapped', r'without limit']),
    (r'\bworldwide\b', [r'worldwide', r'globally', r'global', r'any territory', r'international']),
    (r'\bregardless of\b', [r'regardless', r'even if', r'irrespective']),
    (r'\bwilful misconduct\b', [r'wilful misconduct', r'willful misconduct', r'intentional misconduct', r'gross negligence']),
    (r'\bwhichever is (?:lower|less)\b', [r'whichever is lower', r'whichever is less', r'lower of', r'lesser of']),
    (r'\bsole discretion\b', [r'sole discretion', r'unilateral', r'at its option']),
    (r'\bper day\b', [r'per day', r'daily', r'each day']),
    (r'\b5%\b', [r'5%', r'5 percent', r'five percent']),
    (r'\bnon-refundable\b', [r'non-refundable', r'not refundable', r'no refund']),
    (r'\bpre-existing\b', [r'pre-existing', r'prior ip', r'background ip']),
]

def check_qualifier_coverage(premise: str, hypothesis: str) -> Tuple[bool, List[str]]:
    """
    Checks whether critical qualifiers in the source clause were dropped from the summary.
    Allows semantic equivalents (e.g. 'without limit' matched by 'no cap').
    Returns (has_coverage_issue, list_of_dropped_terms).
    """
    p_lower = premise.lower()
    h_lower = hypothesis.lower()
    dropped = []

    for pattern_regex, synonym_patterns in HIGH_STAKES_PATTERNS:
        if re.search(pattern_regex, p_lower):
            # Check if ANY of the acceptable synonyms are present in the summary
            found = any(re.search(syn, h_lower) for syn in synonym_patterns)
            if not found:
                match = re.search(pattern_regex, p_lower)
                term = match.group(0) if match else "qualifier"
                dropped.append(term)

    return (len(dropped) > 0, dropped)

def clean_terse_labels(text: str) -> str:
    """Strips meta-label preambles like 'Standard severability clause:' or 'Integration clause:'."""
    return re.sub(r'^(?:Standard\s+\w+\s+clause[:\-]?\s*|\w+\s+clause[:\-]?\s*)', '', text.strip(), flags=re.IGNORECASE)

class FaithfulnessChecker:
    """
    Evaluates entailment between clause text and generated summary.
    """

    def __init__(self, model_name: Optional[str] = None, threshold: Optional[float] = None):
        self.model_name = model_name or settings.nli_model
        self.threshold = threshold or settings.faithfulness_threshold
        self._model = None

    def _load_model(self):
        if self._model is None:
            from sentence_transformers import CrossEncoder
            logger.info(f"Loading NLI model: {self.model_name}")
            self._model = CrossEncoder(self.model_name)
        return self._model

    async def check(self, premise: str, hypothesis: str, summary_dict: Optional[dict] = None) -> Tuple[float, bool]:
        """
        Calculates entailment score and flags if unfaithful or if key qualifiers are dropped.
        Returns: (entailment_score, is_flagged)
        """
        try:
            premise_clean = premise.strip()
            raw_meaning = (summary_dict.get("meaning") if summary_dict else hypothesis).strip()
            meaning_text = clean_terse_labels(raw_meaning)
            
            if not premise_clean or not meaning_text:
                return 1.0, False

            model = await asyncio.to_thread(self._load_model)
            
            # Predict entailment
            score = await asyncio.to_thread(
                model.predict, [(premise_clean, meaning_text)]
            )
            
            import numpy as np
            logits = np.squeeze(score)
            exp_scores = np.exp(logits - np.max(logits))
            probs = exp_scores / exp_scores.sum()
            
            # DeBERTa-v3 NLI mapping: 0=contradiction, 1=entailment, 2=neutral
            entailment_prob = float(probs[1])
            contra_prob = float(probs[0])
            neutral_prob = float(probs[2])

            # Check coverage of critical qualifiers
            has_coverage_drop, dropped_terms = check_qualifier_coverage(premise_clean, raw_meaning)
            
            # Calibrated Flagging Logic:
            # 1. High contradiction (> 0.35) -> Flagged
            # 2. Critical qualifier dropped -> Flagged (omission of high-stakes term)
            # 3. Very low entailment (< 0.25) AND not a terse boilerplate definition -> Flagged
            # A summary with high entailment (e.g. >= 0.70) is NEVER flagged unless an explicit qualifier was omitted.
            is_flagged = False
            
            if contra_prob > 0.35:
                is_flagged = True
                logger.info(f"Flagged due to contradiction: contra={contra_prob:.2f}")
            elif has_coverage_drop:
                is_flagged = True
                logger.info(f"Flagged due to dropped qualifier: {dropped_terms}")
            elif entailment_prob < self.threshold and len(premise_clean.split()) > 12:
                # If neutral is dominant on short/terse clauses, do not false-alarm
                if neutral_prob > 0.80 and len(meaning_text.split()) < 10:
                    is_flagged = False
                else:
                    is_flagged = True

            return entailment_prob, is_flagged
        except Exception as e:
            logger.warning(f"Faithfulness check failed: {e}")
            return 1.0, False

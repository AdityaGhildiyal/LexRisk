"""
Fixed-schema clause summarizer.
Outputs: meaning / obligor / trigger / consequence per clause.
"""
import logging
from typing import Optional
from app.models.clause import Clause, ClauseSummary
from app.services.llm_client import summarize_clause
from app.services.cache import RedisCache

logger = logging.getLogger(__name__)

class ClauseSummarizer:
    """Generates plain-language summaries for extracted clauses."""

    def __init__(self, cache: Optional[RedisCache] = None):
        self.cache = cache

    async def summarize(self, clause: Clause, faithfulness_checker=None) -> ClauseSummary:
        """Summarize a single clause, with caching and optional faithfulness check."""
        # Check cache
        if self.cache:
            cached = await self.cache.get("summary", clause.text)
            if cached:
                logger.debug(f"Summary cache hit for clause {clause.id}")
                return ClauseSummary(clause_id=clause.id, **cached)
        
        # Check if summary was already generated in the single-pass extraction step
        if getattr(clause, "pre_summary", None) and isinstance(clause.pre_summary, dict) and clause.pre_summary.get("meaning"):
            raw_summary = clause.pre_summary
        else:
            # Fallback to separate call if missing
            from app.services.llm_client import summarize_clause
            raw_summary = await summarize_clause(clause.text)
        
        # Faithfulness check with qualifier coverage
        faithfulness_score = 1.0
        faithfulness_flag = False
        if faithfulness_checker:
            faithfulness_score, faithfulness_flag = await faithfulness_checker.check(
                premise=clause.text,
                hypothesis=self._summary_to_text(raw_summary),
                summary_dict=raw_summary
            )
        
        summary_data = {
            "meaning": raw_summary.get("meaning", ""),
            "obligor": raw_summary.get("obligor", ""),
            "trigger": raw_summary.get("trigger", ""),
            "consequence": raw_summary.get("consequence", ""),
            "faithfulness_score": faithfulness_score,
            "faithfulness_flag": faithfulness_flag,
        }
        
        # Cache result
        if self.cache:
            await self.cache.set("summary", clause.text, summary_data)
        
        return ClauseSummary(clause_id=clause.id, **summary_data)

    def _summary_to_text(self, summary: dict) -> str:
        """Convert structured summary to a single text for NLI checking."""
        parts = [
            summary.get("meaning", ""),
            f"The obligor is {summary.get('obligor', '')}.",
            f"This is triggered by {summary.get('trigger', '')}.",
            f"The consequence is {summary.get('consequence', '')}.",
        ]
        return ' '.join(p for p in parts if p.strip())

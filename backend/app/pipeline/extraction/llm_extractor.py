"""
LLM-based clause extractor with deduplication and span normalization.
"""
import logging
from typing import List, Optional
from app.models.clause import Chunk, Clause
from app.services.llm_client import extract_clauses_from_text
from app.services.cache import RedisCache

logger = logging.getLogger(__name__)

KNOWN_CLAUSE_TYPES = {
    "indemnity", "limitation_of_liability", "ip_assignment", "termination",
    "governing_law", "dispute_resolution", "confidentiality", "payment",
    "warranty", "force_majeure", "non_compete", "liquidated_damages",
    "notice", "boilerplate", "other"
}

def normalize_text_fingerprint(text: str) -> str:
    """Normalize text to catch identical repeating clauses/footers."""
    import re
    return re.sub(r'\s+', ' ', text.strip().lower())

class LLMExtractor:
    """Extracts, validates, and deduplicates substantive legal clauses."""

    def __init__(self, cache: Optional[RedisCache] = None):
        self.cache = cache

    async def extract(self, chunks: List[Chunk]) -> List[Clause]:
        """Extract clauses across all chunks with full deduplication."""
        all_clauses = []
        seen_fingerprints = set()

        for chunk in chunks:
            clauses = await self._extract_chunk(chunk)
            for c in clauses:
                fp = normalize_text_fingerprint(c.text)
                # Ignore short fragments under 25 chars or exact duplicates
                if len(fp) < 25 or fp in seen_fingerprints:
                    continue
                seen_fingerprints.add(fp)
                all_clauses.append(c)

        return all_clauses

    async def _extract_chunk(self, chunk: Chunk) -> List[Clause]:
        """Extract clauses from a single chunk, with Redis caching."""
        if self.cache:
            cached = await self.cache.get("extract", chunk.text)
            if cached:
                logger.debug(f"Cache hit for chunk {chunk.id}")
                return [Clause(**c, chunk_id=chunk.id) for c in cached]

        raw_clauses = await extract_clauses_from_text(chunk.text)

        clauses = []
        for raw in raw_clauses:
            clause_type = raw.get("clause_type", "other").lower().replace(" ", "_")
            if clause_type not in KNOWN_CLAUSE_TYPES:
                clause_type = "other"

            span_text = raw.get("span", "").strip()
            if not span_text or len(span_text) < 25:
                continue

            confidence = float(raw.get("confidence", 1.0))

            clause = Clause(
                chunk_id=chunk.id,
                text=span_text,
                clause_type=clause_type,
                span=span_text,
                confidence=confidence,
                section=chunk.section_heading,
                pre_summary=raw.get("summary"),
            )
            clauses.append(clause)

        if self.cache and clauses:
            await self.cache.set(
                "extract",
                chunk.text,
                [{"clause_type": c.clause_type, "span": c.span, "confidence": c.confidence, "text": c.text, "pre_summary": c.pre_summary} for c in clauses]
            )

        return clauses

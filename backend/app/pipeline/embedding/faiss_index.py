"""
FAISS index manager.
Maintains one IndexFlatL2 per clause type (partitioned index).
Built offline by corpus/build_index.py; loaded at startup.
"""
import os
import json
import logging
import numpy as np
from typing import Dict, List, Tuple, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class FAISSIndex:
    """
    Manages per-clause-type FAISS indexes for semantic deviation scoring.
    """

    def __init__(self, index_dir: str):
        self.index_dir = Path(index_dir)
        self.indexes: Dict[str, any] = {}  # clause_type -> faiss.Index
        self.stats: Dict[str, dict] = {}  # clause_type -> {mean, std} for z-score normalization
        self._load_indexes()

    def _load_indexes(self):
        """Load all pre-built FAISS indexes from disk."""
        import faiss
        if not self.index_dir.exists():
            logger.warning(f"FAISS index directory not found: {self.index_dir}. Deviation scores will be 0.")
            return
        
        for index_file in self.index_dir.glob("*.faiss"):
            clause_type = index_file.stem
            try:
                self.indexes[clause_type] = faiss.read_index(str(index_file))
                stats_file = self.index_dir / f"{clause_type}_stats.json"
                if stats_file.exists():
                    with open(stats_file) as f:
                        self.stats[clause_type] = json.load(f)
                logger.info(f"Loaded FAISS index for clause type: {clause_type} ({self.indexes[clause_type].ntotal} vectors)")
            except Exception as e:
                logger.error(f"Failed to load index {index_file}: {e}")

    def query(self, clause_type: str, embedding: np.ndarray, k: int = 5) -> Tuple[float, float, List[int]]:
        """
        Query the index for the given clause type.
        Returns (deviation_score, percentile, nearest_neighbor_indices).
        deviation_score is z-score normalized mean distance to k nearest neighbors.
        """
        index = self.indexes.get(clause_type) or self.indexes.get("other")
        if index is None:
            logger.warning(f"No FAISS index for clause type: {clause_type}")
            return 0.5, 50.0, []
        
        embedding = np.array([embedding], dtype=np.float32)
        k = min(k, index.ntotal)
        distances, indices = index.search(embedding, k)
        
        mean_dist = float(np.mean(distances[0]))
        
        # Z-score normalize if stats available
        stats = self.stats.get(clause_type, {})
        if stats.get("mean") and stats.get("std") and stats["std"] > 0:
            deviation = (mean_dist - stats["mean"]) / stats["std"]
            # Convert to [0, 1] with sigmoid
            import math
            deviation_normalized = 1 / (1 + math.exp(-deviation))
        else:
            # Fallback: normalize by a rough max distance heuristic
            deviation_normalized = min(mean_dist / 100.0, 1.0)
        
        percentile = deviation_normalized * 100.0
        return deviation_normalized, percentile, indices[0].tolist()

    def is_available(self, clause_type: str) -> bool:
        return clause_type in self.indexes or "other" in self.indexes

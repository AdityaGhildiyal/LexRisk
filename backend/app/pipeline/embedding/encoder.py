"""
Sentence-Transformers encoder wrapper.
Model: all-mpnet-base-v2 (strong general-purpose baseline, no fine-tuning required).
"""
import logging
import asyncio
import numpy as np
from typing import List, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

class ClauseEncoder:
    """Encodes clause texts into dense vector representations."""

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.sentence_transformer_model
        self._model = None

    def _load_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading encoder: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
        return self._model

    async def encode(self, texts: List[str]) -> np.ndarray:
        """Encode a list of texts into embeddings. Shape: (n, embedding_dim)."""
        model = await asyncio.to_thread(self._load_model)
        embeddings = await asyncio.to_thread(model.encode, texts, show_progress_bar=False)
        return np.array(embeddings, dtype=np.float32)

    async def encode_single(self, text: str) -> np.ndarray:
        """Encode a single text. Shape: (embedding_dim,)."""
        result = await self.encode([text])
        return result[0]

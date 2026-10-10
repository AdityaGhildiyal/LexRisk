from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Dict


CLAUSE_TYPE_WEIGHTS: Dict[str, float] = {
    "indemnity": 0.85,
    "liquidated_damages": 0.85,
    "limitation_of_liability": 0.80,
    "ip_assignment": 0.80,
    "non_compete": 0.80,
    "non_solicit": 0.65,
    "termination": 0.60,
    "term_renewal": 0.45,
    "assignment": 0.55,
    "confidentiality": 0.50,
    "warranty": 0.50,
    "dispute_resolution": 0.45,
    "payment": 0.45,
    "force_majeure": 0.35,
    "governing_law": 0.25,
    "notice": 0.20,
    "boilerplate": 0.15,
    "other": 0.40,
}


class Settings(BaseSettings):
    gemini_api_key: str = ""
    redis_url: str = "redis://redis:6379"
    faiss_index_dir: str = "/app/corpus/indexes"
    llm_model: str = "gemini-3.1-flash-lite"
    sentence_transformer_model: str = "all-mpnet-base-v2"
    nli_model: str = "cross-encoder/nli-deberta-v3-small"
    faithfulness_threshold: float = 0.5
    chunk_window_size: int = 5
    chunk_overlap: int = 2
    knn_k: int = 5
    clause_type_weights: Dict[str, float] = Field(
        default_factory=lambda: CLAUSE_TYPE_WEIGHTS
    )

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()

"""
Offline script to build the FAISS reference index from CUAD + LEDGAR.

Usage:
    python corpus/build_index.py --cuad-path /data/cuad --ledgar-path /data/ledgar --output /app/corpus/indexes

This script runs ONCE (or when the corpus is updated) and saves per-clause-type
FAISS indexes and normalization stats to the output directory.
"""
import argparse
import json
import logging
import os
import numpy as np
from pathlib import Path
from typing import Dict, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

KNOWN_TYPES = [
    "indemnity", "limitation_of_liability", "ip_assignment", "termination",
    "governing_law", "dispute_resolution", "confidentiality", "payment",
    "warranty", "force_majeure", "notice", "boilerplate", "other"
]

def load_cuad_clauses(cuad_path: str) -> Dict[str, List[str]]:
    """Load CUAD clauses partitioned by clause type."""
    clauses_by_type: Dict[str, List[str]] = {t: [] for t in KNOWN_TYPES}
    cuad_path = Path(cuad_path)
    
    if not cuad_path.exists():
        logger.warning(f"CUAD path not found: {cuad_path}")
        return clauses_by_type
    
    # CUAD comes as a JSON file with contract annotations
    for json_file in cuad_path.glob("**/*.json"):
        try:
            with open(json_file) as f:
                data = json.load(f)
            # CUAD format: {"data": [{"paragraphs": [{"qas": [{"question": ..., "answers": [...]}]}]}]}
            if "data" in data:
                for item in data["data"]:
                    for para in item.get("paragraphs", []):
                        for qa in para.get("qas", []):
                            # Map CUAD question to clause type
                            clause_type = _map_cuad_question_to_type(qa.get("question", ""))
                            for answer in qa.get("answers", []):
                                text = answer.get("text", "").strip()
                                if text and len(text) > 20:
                                    clauses_by_type[clause_type].append(text)
        except Exception as e:
            logger.warning(f"Error loading {json_file}: {e}")
    
    total = sum(len(v) for v in clauses_by_type.values())
    logger.info(f"Loaded {total} CUAD clauses")
    return clauses_by_type

def _map_cuad_question_to_type(question: str) -> str:
    """Map CUAD question text to our clause type taxonomy."""
    q = question.lower()
    if "indemnif" in q: return "indemnity"
    if "limitation" in q or "liability cap" in q: return "limitation_of_liability"
    if "intellectual property" in q or "ip" in q or "assignment" in q: return "ip_assignment"
    if "terminat" in q: return "termination"
    if "governing law" in q or "jurisdiction" in q: return "governing_law"
    if "arbitration" in q or "dispute" in q: return "dispute_resolution"
    if "confidential" in q or "non-disclosure" in q: return "confidentiality"
    if "payment" in q or "fee" in q or "price" in q: return "payment"
    if "warrant" in q: return "warranty"
    if "force majeure" in q: return "force_majeure"
    if "notice" in q: return "notice"
    return "other"

def build_faiss_indexes(clauses_by_type: Dict[str, List[str]], output_dir: str, model_name: str = "all-mpnet-base-v2"):
    """Build and save FAISS indexes for each clause type."""
    import faiss
    from sentence_transformers import SentenceTransformer
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Loading encoder: {model_name}")
    model = SentenceTransformer(model_name)
    
    for clause_type, texts in clauses_by_type.items():
        if len(texts) < 2:
            logger.warning(f"Skipping {clause_type}: only {len(texts)} clauses (need at least 2)")
            continue
        
        logger.info(f"Building index for {clause_type}: {len(texts)} clauses")
        
        # Encode all clauses
        embeddings = model.encode(texts, show_progress_bar=True, batch_size=32)
        embeddings = np.array(embeddings, dtype=np.float32)
        
        # Build FAISS index
        dim = embeddings.shape[1]
        index = faiss.IndexFlatL2(dim)
        index.add(embeddings)
        
        # Save index
        faiss.write_index(index, str(output_dir / f"{clause_type}.faiss"))
        
        # Compute and save normalization stats
        # Sample pairwise distances for z-score normalization
        sample_size = min(500, len(texts))
        sample_idx = np.random.choice(len(texts), sample_size, replace=False)
        sample_embs = embeddings[sample_idx]
        dists, _ = index.search(sample_embs, min(6, index.ntotal))
        # Exclude self-distance (distance=0 at index 0)
        neighbor_dists = dists[:, 1:].flatten()
        stats = {
            "mean": float(np.mean(neighbor_dists)),
            "std": float(np.std(neighbor_dists)),
            "count": len(texts),
        }
        with open(output_dir / f"{clause_type}_stats.json", "w") as f:
            json.dump(stats, f, indent=2)
        
        logger.info(f"  Saved {clause_type}.faiss ({index.ntotal} vectors, dim={dim})")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build LexRisk FAISS reference index")
    parser.add_argument("--cuad-path", default="/data/cuad", help="Path to CUAD dataset")
    parser.add_argument("--ledgar-path", default="/data/ledgar", help="Path to LEDGAR dataset")
    parser.add_argument("--output", default="/app/corpus/indexes", help="Output directory for indexes")
    parser.add_argument("--model", default="all-mpnet-base-v2", help="Sentence transformer model")
    args = parser.parse_args()
    
    all_clauses: Dict[str, List[str]] = {t: [] for t in KNOWN_TYPES}
    
    # Load CUAD
    cuad_clauses = load_cuad_clauses(args.cuad_path)
    for clause_type, texts in cuad_clauses.items():
        all_clauses[clause_type].extend(texts)
    
    # Build indexes
    build_faiss_indexes(all_clauses, args.output, model_name=args.model)
    logger.info("Index build complete.")

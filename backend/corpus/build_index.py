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
    "indemnity", "limitation_of_liability", "ip_assignment", "non_compete",
    "non_solicit", "liquidated_damages", "termination", "term_renewal",
    "assignment", "confidentiality", "governing_law", "dispute_resolution",
    "warranty", "payment", "force_majeure", "notice", "boilerplate", "other"
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
    if "limitation of liability" in q or "liability cap" in q or "uncapped" in q: return "limitation_of_liability"
    if "non-compete" in q or "noncompete" in q or "restriction on ability to compete" in q: return "non_compete"
    if "non-solicit" in q or "nonsolicit" in q or "non-disparagement" in q: return "non_solicit"
    if "liquidated damages" in q or "damage cap" in q: return "liquidated_damages"
    if "renewal" in q: return "term_renewal"
    if "termination" in q: return "termination"
    if "ip" in q or "intellectual property" in q or "patent" in q or "trademark" in q: return "ip_assignment"
    if "assignment" in q: return "assignment"
    if "governing law" in q or "jurisdiction" in q: return "governing_law"
    if "arbitration" in q or "dispute" in q: return "dispute_resolution"
    if "confidential" in q or "non-disclosure" in q: return "confidentiality"
    if "payment" in q or "fee" in q or "price" in q or "revenue" in q: return "payment"
    if "warrant" in q: return "warranty"
    if "force majeure" in q: return "force_majeure"
    if "notice" in q: return "notice"
    if "severability" in q or "entire agreement" in q or "counterparts" in q: return "boilerplate"
    return "other"


def load_ledgar_clauses(ledgar_path: str) -> Dict[str, List[str]]:
    """Load LEDGAR provisions partitioned by mapped clause types."""
    clauses_by_type: Dict[str, List[str]] = {t: [] for t in KNOWN_TYPES}
    ledgar_path = Path(ledgar_path)
    
    if not ledgar_path.exists():
        logger.warning(f"LEDGAR path not found: {ledgar_path}")
        return clauses_by_type

    parquet_files = list(ledgar_path.glob("**/*.parquet"))
    if not parquet_files:
        logger.warning(f"No parquet files found in {ledgar_path}")
        return clauses_by_type

    try:
        import pyarrow.parquet as pq
        for pfile in parquet_files:
            table = pq.read_table(str(pfile))
            # Extract label names from Hugging Face metadata
            metadata = table.schema.metadata or {}
            label_names = []
            for k, v in metadata.items():
                if b"label" in v:
                    try:
                        meta_dict = json.loads(v.decode("utf-8"))
                        label_names = meta_dict.get("info", {}).get("features", {}).get("label", {}).get("names", [])
                        if label_names:
                            break
                    except Exception:
                        pass
            
            # Map LEDGAR class names to LexRisk taxonomy
            # LEDGAR includes 100 clause categories
            for text_val, label_val in zip(table["text"], table["label"]):
                text = text_val.as_py()
                if not text or len(text.strip()) < 25:
                    continue
                label_idx = label_val.as_py()
                name = label_names[label_idx].lower() if label_names and label_idx < len(label_names) else ""
                
                target_type = None
                if "indemnif" in name or "indemnity" in name:
                    target_type = "indemnity"
                elif "limitation" in name:
                    target_type = "limitation_of_liability"
                elif "governing law" in name or "jurisdiction" in name or "submission to jurisdiction" in name or "venue" in name:
                    target_type = "governing_law"
                elif "arbitration" in name or "dispute" in name or "waiver of jury" in name:
                    target_type = "dispute_resolution"
                elif "confidential" in name:
                    target_type = "confidentiality"
                elif "termination" in name:
                    target_type = "termination"
                elif "intellectual property" in name:
                    target_type = "ip_assignment"
                elif "assignment" in name:
                    target_type = "assignment"
                elif "non-disparagement" in name:
                    target_type = "non_solicit"
                elif "notice" in name:
                    target_type = "notice"
                elif "warranty" in name or "warranties" in name:
                    target_type = "warranty"
                elif "payment" in name or "fee" in name:
                    target_type = "payment"
                elif any(bp in name for bp in ["severability", "entire agreement", "counterpart", "integration", "heading"]):
                    target_type = "boilerplate"
                elif "term" in name:
                    target_type = "term_renewal"
                
                if target_type and target_type in clauses_by_type:
                    # Keep diverse, high-quality samples up to 1500 per type to maintain balanced index size
                    if len(clauses_by_type[target_type]) < 1500:
                        clauses_by_type[target_type].append(text.strip())

        total = sum(len(v) for v in clauses_by_type.values())
        logger.info(f"Loaded {total} LEDGAR clauses")
    except Exception as e:
        logger.warning(f"Error loading LEDGAR clauses: {e}")

    return clauses_by_type

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
    
    # Load LEDGAR
    ledgar_clauses = load_ledgar_clauses(args.ledgar_path)
    for clause_type, texts in ledgar_clauses.items():
        all_clauses[clause_type].extend(texts)
    
    # Deduplicate within each clause type
    for clause_type in all_clauses:
        unique = list(dict.fromkeys(all_clauses[clause_type]))
        all_clauses[clause_type] = unique
        logger.info(f"Total unique reference clauses for '{clause_type}': {len(unique)}")

    # Build indexes
    build_faiss_indexes(all_clauses, args.output, model_name=args.model)
    logger.info("Index build complete.")

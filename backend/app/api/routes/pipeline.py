"""
Primary pipeline endpoint: POST /pipeline/process
Runs the full pipeline: upload → chunk → extract → summarize → embed → score → report
"""
import logging
from fastapi import APIRouter, UploadFile, File, Request, HTTPException
from app.models.risk_report import RiskReport, ClauseReport
from app.pipeline.chunking.sentence_window import parse_document, chunk_document
from app.pipeline.extraction.llm_extractor import LLMExtractor
from app.pipeline.summarization.summarizer import ClauseSummarizer
from app.pipeline.summarization.faithfulness import FaithfulnessChecker
from app.pipeline.embedding.encoder import ClauseEncoder
from app.pipeline.risk.scorer import score_clause
from app.models.clause import DeviationResult
from app.core.config import settings
import uuid
from datetime import datetime

router = APIRouter()
logger = logging.getLogger(__name__)

_encoder = ClauseEncoder()
_faithfulness_checker = FaithfulnessChecker()

@router.post("/process", response_model=RiskReport)
async def process_contract(request: Request, file: UploadFile = File(...)):
    """
    Full pipeline: contract file → risk-ranked report.
    """
    content_type = file.content_type or ""
    file_bytes = await file.read()
    
    if not file_bytes:
        raise HTTPException(400, "Empty file uploaded")
    
    logger.info(f"Processing contract: {file.filename} ({len(file_bytes)} bytes)")
    
    # Stage 1: Parse & Chunk
    try:
        doc_text = parse_document(file_bytes, content_type)
    except Exception as e:
        raise HTTPException(422, f"Failed to parse document: {e}")
    
    chunks = chunk_document(doc_text)
    logger.info(f"Created {len(chunks)} chunks")
    
    # Stage 2: Extract clauses
    cache = getattr(request.app.state, "cache", None)
    extractor = LLMExtractor(cache=cache)
    clauses = await extractor.extract(chunks)
    logger.info(f"Extracted {len(clauses)} clauses")
    
    if not clauses:
        raise HTTPException(422, "No clauses could be extracted from this document")
    
    # Stage 3: Summarize + faithfulness check
    summarizer = ClauseSummarizer(cache=cache)
    summaries = {}
    for clause in clauses:
        summary = await summarizer.summarize(clause, faithfulness_checker=_faithfulness_checker)
        summaries[clause.id] = summary
    
    # Stage 4: Embed + deviation scoring
    faiss_index = getattr(request.app.state, "faiss_index", None)
    clause_texts = [c.text for c in clauses]
    embeddings = await _encoder.encode(clause_texts)
    
    deviation_results = {}
    for i, clause in enumerate(clauses):
        if faiss_index and faiss_index.is_available(clause.clause_type):
            dev_score, percentile, nn_ids = faiss_index.query(
                clause.clause_type, embeddings[i], k=settings.knn_k
            )
            is_comp = True
        else:
            dev_score, percentile, nn_ids = None, None, []
            is_comp = False
        
        deviation_results[clause.id] = DeviationResult(
            clause_id=clause.id,
            deviation_score=dev_score,
            percentile=percentile,
            is_computed=is_comp,
            nearest_neighbor_ids=[str(x) for x in nn_ids],
        )
    
    # Stage 5: Risk scoring
    risk_scores = {}
    for clause in clauses:
        risk_score = score_clause(clause, deviation_results[clause.id])
        risk_scores[clause.id] = risk_score
    
    # Assemble report
    clause_reports = []
    for clause in clauses:
        summary = summaries[clause.id]
        risk = risk_scores[clause.id]
        clause_reports.append(ClauseReport(
            clause_id=clause.id,
            clause_type=clause.clause_type,
            text=clause.text,
            section=clause.section,
            summary=summary.model_dump(),
            deviation_score=deviation_results[clause.id].deviation_score,
            risk_score=risk.risk_score,
            risk_rationale=risk.rationale,
        ))
    
    # Sort by risk score descending
    clause_reports.sort(key=lambda x: x.risk_score, reverse=True)
    
    high_risk = sum(1 for c in clause_reports if c.risk_score >= 0.6)
    faith_flags = sum(1 for c in clause_reports if c.summary.get("faithfulness_flag", False))
    
    return RiskReport(
        contract_id=str(uuid.uuid4()),
        generated_at=datetime.utcnow().isoformat(),
        clauses=clause_reports,
        total_clauses=len(clause_reports),
        high_risk_count=high_risk,
        faithfulness_flags=faith_flags,
    )

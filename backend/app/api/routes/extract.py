from fastapi import APIRouter, UploadFile, File, Request
from app.pipeline.chunking.sentence_window import parse_document, chunk_document
from app.pipeline.extraction.llm_extractor import LLMExtractor
from app.models.clause import Clause
from typing import List

router = APIRouter()

@router.post("/extract", response_model=List[Clause])
async def extract_clauses(request: Request, file: UploadFile = File(...)):
    """Stage endpoint: extract clauses from an uploaded contract file."""
    file_bytes = await file.read()
    doc_text = parse_document(file_bytes, file.content_type or "")
    chunks = chunk_document(doc_text)
    cache = getattr(request.app.state, "cache", None)
    extractor = LLMExtractor(cache=cache)
    clauses = await extractor.extract(chunks)
    return clauses

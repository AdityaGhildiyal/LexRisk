# LexRisk — Low-Level Design

**Implementation-level detail: API contracts, data models, module design, error handling.**

## 1. API Contracts

### 1.1 Express (web) routes

| Method | Route | Purpose |
|---|---|---|
| GET | `/` | Upload form |
| POST | `/upload` | Accepts multipart file, forwards to backend, redirects to `/report/:id` |
| GET | `/report/:id` | Renders the risk report |

### 1.2 FastAPI endpoints

**`POST /pipeline/process`** — primary endpoint, runs the full pipeline.
- Request: multipart file (`.pdf` or `.docx`)
- Response: `RiskReport` JSON (schema below)

**`POST /extract`, `POST /summarize`, `POST /score`** — granular endpoints, useful for testing individual pipeline stages during Phases 1–4 even though the web layer only calls `/pipeline/process`.

Example `RiskReport` response shape:
```json
{
  "contract_id": "string",
  "generated_at": "ISO-8601 timestamp",
  "clauses": [
    {
      "clause_id": "string",
      "clause_type": "string",
      "text": "string",
      "section": "string | null",
      "summary": {
        "meaning": "string",
        "obligor": "string",
        "trigger": "string",
        "consequence": "string",
        "faithfulness_score": 0.0,
        "faithfulness_flag": false
      },
      "deviation_score": 0.0,
      "risk_score": 0.0,
      "risk_rationale": "string"
    }
  ]
}
```

## 2. Data Models (Pydantic)

- `Chunk`: `{ text, section_heading, page_number, char_range }`
- `Clause`: `{ id, chunk_id, text, clause_type, span, confidence }`
- `ClauseSummary`: `{ clause_id, meaning, obligor, trigger, consequence, faithfulness_score, faithfulness_flag }`
- `DeviationResult`: `{ clause_id, deviation_score, percentile, nearest_neighbor_ids }`
- `RiskScore`: `{ clause_id, risk_score, clause_type_weight, rationale }`
- `RiskReport`: `{ contract_id, generated_at, clauses: List[...] }`

## 3. Module Design

### 3.1 Chunking (`pipeline/chunking/`)
- Input: raw file bytes + MIME type.
- Output: `List[Chunk]`.
- Default strategy: sentence-window chunking with overlap (configurable window/overlap size).
- `layout_parser.py` (Phase 1 stretch): heading/section-number detection, swapped in behind the same interface once ready.

### 3.2 Extraction (`pipeline/extraction/`)
- Interface: `Extractor.extract(chunks: List[Chunk]) -> List[Clause]`.
- `llm_extractor.py` (primary): schema-constrained prompt, JSON-validated output, cache-checked via Redis before calling the LLM.
- `finetuned_classifier.py` (Phase 6 stretch): implements the same interface, so it's a drop-in alternative for the benchmark comparison — orchestration code never needs to know which one is active.

### 3.3 Summarization + Faithfulness (`pipeline/summarization/`)
- `summarizer.py`: one LLM call per clause, fixed schema (meaning / obligor / trigger / consequence), cache-checked the same way as extraction.
- `faithfulness.py`: NLI entailment check between clause text (premise) and summary (hypothesis); below-threshold entailment sets `faithfulness_flag = true`.

### 3.4 Embedding + FAISS (`pipeline/embedding/`)
- `encoder.py`: wraps `all-mpnet-base-v2` (Sentence-Transformers), no fine-tuning.
- `faiss_index.py`: one `IndexFlatL2` per clause type (partitioned); `build_index.py` under `corpus/` builds these offline from CUAD (+ LEDGAR).
- Deviation score: normalized (percentile or z-score) distance to k-nearest-neighbors within the clause's own type partition — never compared across types.

### 3.5 Risk Scoring (`pipeline/risk/scorer.py`)
- `risk_score = w1 * normalized_deviation + w2 * clause_type_weight`
- `clause_type_weight` sourced from a static rubric (indemnity, limitation-of-liability, IP-assignment weighted higher than notice/boilerplate clauses); kept as a small config table, not learned, until/unless Phase 5 labeled data supports a learned version.
- Kept as a weighted sum or small logistic regression — never a model whose output can't be traced back to the two inputs.

## 4. Cache Schema (Redis)

| Key pattern | Value | Purpose |
|---|---|---|
| `extract:{sha256(clause_text)}` | Extraction result JSON | Avoid re-calling the LLM for identical clause text |
| `summary:{sha256(clause_text)}` | Summary + faithfulness JSON | Same, for summarization |

No TTL needed for the academic-demo scope; can be added later if the corpus/cache needs periodic refresh.

## 5. Error Handling

| Case | Handling |
|---|---|
| Unparseable/malformed upload | FastAPI returns 422 with a message; Express shows a friendly error, doesn't crash the upload flow |
| LLM API failure | Retry with backoff (2 attempts), then mark that clause as `extraction_failed` rather than failing the whole report |
| Low-confidence extraction | Included in the report, flagged as low-confidence rather than silently dropped — a paralegal should see it and judge for themselves |
| FAISS index missing/not built | Fail fast at startup with a clear error, not a silent zero deviation score |

## 6. Sequence — Upload to Report

1. User uploads a file via Express `/upload`.
2. Express forwards it as multipart to FastAPI `/pipeline/process`.
3. FastAPI chunks the document.
4. For each chunk: extract (cache-checked) → clause list.
5. For each clause: summarize + faithfulness-check (cache-checked).
6. For each clause: embed → FAISS query (same clause-type partition) → deviation score.
7. For each clause: deviation score + clause-type weight → risk score.
8. FastAPI assembles and returns the `RiskReport`.
9. Express renders `/report/:id`.

# LexRisk

> **AI-powered contract risk analysis** — B.Tech Final Year Project (CSE, 2023–2027)

LexRisk is a contract-review assistant that takes an uploaded contract (PDF/DOCX) and returns a risk-annotated, plain-language report. It combines clause-level extraction via an LLM with a corpus-grounded semantic anomaly signal, so instead of just listing what's in a contract, it surfaces **which clauses are unusual** relative to how that clause type is normally written.

## Architecture

```
Browser → Express (:3000) → FastAPI (:8000) → Redis (:6379)
                                            → FAISS Index (local)
                                            → Gemini API (external)
```

**Pipeline stages (per contract):**
1. **Chunking** — Sentence-window chunker splits document into overlapping chunks
2. **Extraction** — Gemini 1.5 Flash extracts typed clauses (JSON-constrained output)
3. **Summarization** — Fixed-schema plain-language summary per clause (meaning / obligor / trigger / consequence)
4. **Faithfulness check** — NLI model (DeBERTa-v3) verifies summaries aren't hallucinated
5. **Embedding** — `all-mpnet-base-v2` encodes each clause
6. **Deviation scoring** — FAISS query against per-clause-type reference index (CUAD + LEDGAR)
7. **Risk scoring** — `risk = 0.6×deviation + 0.4×clause_type_weight` (interpretable weighted sum)

## Quick Start

### Prerequisites
- Docker Desktop (running)
- A Gemini API key (get one at [aistudio.google.com](https://aistudio.google.com))

### 1. Set up environment

```bash
# Backend
cp backend/.env.example backend/.env
# Edit backend/.env and set your GEMINI_API_KEY

# Web
cp web/.env.example web/.env
```

### 2. Start everything

```bash
docker-compose up --build
```

- **Web UI**: http://localhost:3000
- **API docs**: http://localhost:8000/docs
- **Health check**: http://localhost:8000/health

### 3. Build the reference corpus index (Phase 3)

Once you have CUAD data downloaded:

```bash
# Download CUAD dataset
# https://www.atticusprojectai.org/cuad

docker-compose run --rm backend python corpus/build_index.py \
  --cuad-path /data/cuad \
  --output /app/corpus/indexes
```

## Development

### Backend (FastAPI)

```bash
cd backend
pip install -r requirements.txt
# Set env vars
export GEMINI_API_KEY=your_key
export REDIS_URL=redis://localhost:6379
uvicorn app.main:app --reload --port 8000
```

### Web (Express)

```bash
cd web
npm install
export BACKEND_URL=http://localhost:8000
npm run dev
```

### Running tests

```bash
# Backend
docker-compose run --rm backend pytest tests/ -v

# Or locally:
cd backend && pytest tests/ -v
```

## Project Phases

| Phase | Status | Description |
|---|---|---|
| 0 | ✅ | Repo scaffold, Docker, environment setup |
| 1 | ✅ | Chunking + LLM extraction MVP |
| 2 | ✅ | Summarization + NLI faithfulness checking |
| 3 | ⏳ | Reference corpus (CUAD+LEDGAR) + FAISS index |
| 4 | ✅ | Risk scoring + full integration + UI |
| 5 | ⏳ | Expert labeling + Spearman's ρ correlation study |
| 6 | ⏳ | Polish, stretch goals, paper, viva prep |

## Clause Types Recognized

`indemnity` · `limitation_of_liability` · `ip_assignment` · `termination` · `governing_law` · `dispute_resolution` · `confidentiality` · `payment` · `warranty` · `force_majeure` · `notice` · `boilerplate` · `other`

## Risk Scoring

Risk score is an **interpretable weighted sum**:

```
risk_score = 0.6 × normalized_deviation + 0.4 × clause_type_weight
```

- **deviation score**: how far the clause embedding is from the reference corpus centroid for that clause type (FAISS k-NN, z-score normalized)
- **clause_type_weight**: static rubric (indemnity=0.9, limitation_of_liability=0.85, ... notice=0.3)

No black-box model — every risk flag traces back to these two values.

## Evaluation Metrics (Phase 5)

- **Extraction F1** vs. CUAD held-out labels
- **Faithfulness pass rate** — % of summaries passing NLI entailment check
- **Spearman's ρ** between system risk ranking and expert-labeled "unusual/not-unusual" judgments (headline metric)

## Repository Structure

```
lexrisk/
├── backend/                    # FastAPI pipeline service
│   ├── app/
│   │   ├── main.py
│   │   ├── api/routes/         # pipeline.py, extract.py, summarize.py, score.py
│   │   ├── core/               # config.py, logging.py
│   │   ├── pipeline/
│   │   │   ├── chunking/       # sentence_window.py
│   │   │   ├── extraction/     # llm_extractor.py
│   │   │   ├── summarization/  # summarizer.py, faithfulness.py
│   │   │   ├── embedding/      # encoder.py, faiss_index.py
│   │   │   └── risk/           # scorer.py
│   │   ├── models/             # clause.py, contract.py, risk_report.py
│   │   └── services/           # cache.py (Redis), llm_client.py (Gemini)
│   ├── corpus/                 # build_index.py, cuad/, ledgar/
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── web/                        # Express web frontend
│   ├── src/
│   │   ├── app.js
│   │   ├── routes/             # upload.js, report.js
│   │   ├── controllers/        # uploadController.js, reportController.js
│   │   ├── services/           # backendClient.js
│   │   ├── views/              # upload.ejs, report.ejs
│   │   └── public/             # css/main.css, js/upload.js, js/report.js
│   └── Dockerfile
├── Considerations/             # PRD, HLD, LLD, Architecture, Roadmap
├── docker-compose.yml
└── README.md
```

## License

Academic project — not for production use.

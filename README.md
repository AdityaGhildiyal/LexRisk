# LexRisk

> **AI-Powered Legal Contract Review & Interpretable Risk Assessment Platform**

LexRisk is an end-to-end contract review and intelligence assistant that takes an uploaded contract (PDF/DOCX) and returns an auditable, plain-language risk report. It combines layout-aware clause extraction with a corpus-grounded semantic anomaly signal, surfacing **which clauses are unusually aggressive or one-sided** relative to empirical legal precedent (CUAD & LEDGAR).

## Key Features & Differentiators

- **Layout & Section-Aware Operative Chunking**: Regex-driven boundary detection splits contracts cleanly by numbered clauses (`7.1`, `8.2`, `ARTICLE IV`) while discarding recurring headers, footers, and pagination noise.
- **Single-Pass Structured Extraction**: Extracts entire verbatim provisions and structured summaries simultaneously without missing critical trailing qualifiers (e.g., unlimited liability, asymmetric non-competes).
- **Local NLI Faithfulness Verification**: Evaluates summary entailment using `cross-encoder/nli-deberta-v3-small` with qualifier coverage checks (catching dropped terms like *"without limit"*, *"worldwide"*, *"sole discretion"*).
- **Transparent Risk Scoring**: Weighted combination of empirical semantic deviation and clause-type criticality. If reference indexes are uncomputed, the system clearly marks them as such without hallucinating baseline metrics.
- **Editorial Paper-Style UI & Formatted Export**: Minimalist, publication-grade reading experience with structured matrices and one-click `.txt` formatted audit reports.

## Architecture

```
Browser (UI) ──> Express.js (:3000) ──> FastAPI (:8000) ──> Redis Cache (:6379)
                                                        ──> Gemini Flash (REST API)
                                                        ──> DeBERTa-v3 Cross-Encoder (Local CPU)
                                                        ──> FAISS Partitioned Vector Index (Local)
```

**Pipeline stages (per contract):**
1. **Header/Footer Stripping & Section Chunking** — Cleans page boundaries and partitions by operative decimal/article sections.
2. **LLM Extraction & Summary (Single-Pass)** — Gemini Flash extracts exact clause spans and 4-field summaries (`meaning`, `obligor`, `trigger`, `consequence`).
3. **NLI Entailment Check** — Cross-Encoder evaluates premise-hypothesis entailment and validates presence of high-stakes qualifiers.
4. **Dense Vector Encoding** — `sentence-transformers/all-mpnet-base-v2` encodes operative text.
5. **Corpus Deviation Scoring** — Queries partitioned FAISS indices (CUAD + LEDGAR) for k-NN distance.
6. **Interpretable Risk Scoring** — Transparent weighted sum (`0.6×deviation + 0.4×type_weight`).
7. **Interactive Audit View & Export** — Risk distribution spectrum, multi-tier filtering, and client-side ASCII `.txt` report downloads.

## Quick Start

### Prerequisites
- Docker Desktop (running)
- A Gemini API key (obtainable at [aistudio.google.com](https://aistudio.google.com))

### 1. Set up environment

```bash
# Backend environment configuration
cp backend/.env.example backend/.env
# Open backend/.env and add: GEMINI_API_KEY=your_key_here

# Web environment configuration
cp web/.env.example web/.env
```

### 2. Start all services

```bash
docker-compose up --build
```

- **Web UI**: [http://localhost:3000](http://localhost:3000)
- **FastAPI OpenAPI Swagger**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health check**: [http://localhost:8000/health](http://localhost:8000/health)

### 3. Build the reference corpus index (Phase 3)

When building the offline empirical reference index with the CUAD / LEDGAR dataset:

```bash
docker-compose run --rm backend python corpus/build_index.py \
  --cuad-path /data/cuad \
  --output /app/corpus/indexes
```

## Development & Local Testing

### Backend (FastAPI)

```bash
cd backend
pip install -r requirements.txt
export GEMINI_API_KEY="your_api_key"
export REDIS_URL="redis://localhost:6379"
uvicorn app.main:app --reload --port 8000
```

### Web (Express.js)

```bash
cd web
npm install
export BACKEND_URL="http://localhost:8000"
npm run dev
```

### End-to-End & Unit Tests

```bash
# Run unit tests inside backend container
docker exec lexrisk-backend-1 pytest tests/ -v

# Run the end-to-end pipeline verification script
python test_pipeline_e2e.py
```

## Project Phases & Progress

| Phase | Status | Description |
|---|---|---|
| 0 | ✅ | Repository scaffold, Docker compose network, environment configuration |
| 1 | ✅ | Numbered section chunking + LLM single-pass extraction MVP |
| 2 | ✅ | Structured 4-field summarization + DeBERTa NLI faithfulness verification |
| 3 | ✅ | Reference corpus ingestion (CUAD v1.0 + LEDGAR) & 16-partition FAISS vector index |
| 4 | ✅ | Interpretable risk scoring engine, editorial UI, and text audit exporter |
| 5 | ✅ | Empirical benchmark: Spearman's rank correlation ($\rho=0.3395, p=0.017$) & NLI pass rate (83.7%) |
| 6 | ✅ | Technical whitepaper, architecture documentation & evaluation presentation deck |

## Clause Taxonomy Recognized

- `indemnity` (Hold harmless, defense, liability assumption)
- `limitation_of_liability` (Consequential damages waiver, aggregate caps)
- `ip_assignment` (Ownership, pre-existing IP, work product transfer)
- `non_compete` (Commercial restrictions, duration/geographic scope)
- `non_solicit` (Employee / client non-solicitation)
- `liquidated_damages` (Daily delay fees, pre-agreed penalties)
- `termination` (Termination for convenience, default, breach)
- `term_renewal` (Auto-renewal periods, notice windows)
- `assignment` (Third-party transfer, change of control)
- `confidentiality` (Non-disclosure scope, standard exceptions)
- `governing_law` (Jurisdiction, choice of law)
- `dispute_resolution` (Arbitration, mediation, jury trial waiver)
- `warranty` (Representations, warranties, disclaimers)
- `payment` (Invoicing, late interest, payment milestones)
- `force_majeure` (Excused non-performance events)
- `notice` & `boilerplate` (Addresses, severability, entire agreement)

## Interpretable Risk Formulation

The risk score is formulated as an explicit, auditable linear combination:

$$\text{Risk Score} = 0.6 \cdot \text{Normalized Deviation} + 0.4 \cdot \text{Clause Type Weight}$$

- **Empirical Deviation**: Derived from $k$-NN distance against the partitioned reference corpus. Uncomputed deviation is explicitly surfaced as *"Uncomputed (Phase 3)"* to avoid synthetic metrics.
- **Risk Tiers**:
  - **Critical**: $\ge 80\%$
  - **High**: $65\% - 79\%$
  - **Moderate**: $35\% - 64\%$
  - **Low**: $< 35\%$

## Evaluation Suite (Phase 5)

- **Extraction Precision & F1**: Evaluated against annotated CUAD evaluation partitions.
- **Faithfulness Pass Rate**: Evaluated with contradiction/entailment cross-encoders and qualifier coverage checks.
- **Spearman's Rank Correlation ($\rho$)**: Comparing computed risk ranking with expert legal review annotations.

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

MIT License — see LICENSE for details. Personal project by Aditya Ghildiyal.

# LexRisk — Architecture Reference

**Practical reference for running and navigating the codebase. See HLD.md for design rationale, LLD.md for implementation detail.**

## 1. Service Topology

```
Express (web, :3000)  ──HTTP──▶  FastAPI (backend, :8000)  ──▶  Redis (:6379)
                                                              ──▶  FAISS index (local files)
                                                              ──▶  LLM API (external)
```

## 2. Repository Structure

```
lexrisk/
├── backend/                          # FastAPI — ML/document pipeline service
│   ├── app/
│   │   ├── main.py                   # app entrypoint
│   │   ├── api/routes/                # extract.py, summarize.py, score.py, pipeline.py
│   │   ├── core/                      # config.py, logging.py
│   │   ├── pipeline/
│   │   │   ├── chunking/              # sentence_window.py, layout_parser.py (stretch)
│   │   │   ├── extraction/            # llm_extractor.py (primary), finetuned_classifier.py (stretch)
│   │   │   ├── summarization/         # summarizer.py, faithfulness.py
│   │   │   ├── embedding/             # encoder.py, faiss_index.py
│   │   │   └── risk/                  # scorer.py
│   │   ├── models/                    # Pydantic schemas — clause.py, contract.py, risk_report.py
│   │   └── services/                  # cache.py (Redis), llm_client.py
│   ├── corpus/                        # cuad/, ledgar/, build_index.py
│   ├── evaluation/                    # extraction_f1.py, faithfulness_eval.py, correlation_study.py
│   ├── tests/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
│
├── web/                               # Express — upload UI + thin client to backend
│   ├── src/
│   │   ├── app.js
│   │   ├── routes/                    # upload.js, report.js
│   │   ├── controllers/               # uploadController.js, reportController.js
│   │   ├── services/                  # backendClient.js — calls FastAPI
│   │   ├── views/                     # EJS templates — upload.ejs, report.ejs
│   │   └── public/                    # css/, js/
│   ├── tests/
│   ├── package.json
│   ├── Dockerfile
│   └── .env.example
│
├── docs/
│   ├── PRD.md
│   ├── HLD.md
│   ├── LLD.md
│   └── Architecture.md
│
├── data/                              # gitignored — sample contracts, local corpus cache
├── .github/workflows/                 # backend-ci.yml, web-ci.yml
├── docker-compose.yml
└── README.md
```

## 3. Communication Contract (summary)

Express calls FastAPI's `POST /pipeline/process` with the uploaded file as multipart form data. FastAPI returns a `RiskReport` JSON object (full schema in LLD.md §2). Express holds this in memory/session for the demo and renders it via the `report.ejs` view — no separate database needed for the MVP.

## 4. Local Development

```bash
docker-compose up --build
```

- Web service → `http://localhost:3000`
- Pipeline service → `http://localhost:8000`
- Redis → `localhost:6379` (internal use only)

Required environment variables (see `.env.example` in each service):
- `LLM_API_KEY` (backend)
- `BACKEND_URL` (web, defaults to `http://backend:8000` inside Docker Compose)
- `REDIS_URL` (backend)

## 5. Deployment Notes

A single-host Docker Compose setup is sufficient for this project's scope — an academic demo and viva, not a production deployment. There's no need for container orchestration (Kubernetes, etc.) or multi-region concerns here.

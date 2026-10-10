# LexRisk — High-Level Design

**Companion to PRD.md — covers system architecture and major design decisions.**

## 1. System Overview

LexRisk is split into two independently runnable services plus supporting infrastructure:

- **Web service** (Node.js + Express) — handles upload, calls the backend, renders the report.
- **Pipeline service** (Python + FastAPI) — owns the actual ML/NLP pipeline: chunking, extraction, summarization, embedding, risk scoring.

This split exists because the ML ecosystem the pipeline depends on (Sentence-Transformers, FAISS, HuggingFace Transformers, NLI models) is Python-native — there's no reasonable way to do that work in Node. Express's job is narrower: own the UI and act as a thin client to the pipeline service.

## 2. Architecture Diagram

```
                    ┌───────────────────────────┐
                    │   Express Web Service      │
                    │  (upload UI, report view)  │
                    └────────────┬────────────────┘
                                 │ HTTP (multipart upload / JSON)
                                 ▼
                    ┌─────────────────────────────┐
                    │   FastAPI Pipeline Service    │
                    │                               │
                    │  Chunking → Extraction →      │
                    │  Summarization+Faithfulness → │
                    │  Embedding → Risk Scoring      │
                    └───────┬───────────┬────────────┘
                            │           │
                   ┌────────▼───┐   ┌───▼──────────────┐
                   │   Redis     │   │  FAISS Index       │
                   │  (LLM call  │   │  (clause-type       │
                   │   cache)    │   │   partitioned,       │
                   └─────────────┘   │   CUAD + LEDGAR)     │
                                     └───────────────────────┘
                            │
                   ┌────────▼──────────┐
                   │   External LLM API  │
                   │ (extraction,         │
                   │  summarization)      │
                   └──────────────────────┘
```

## 3. Components

| Component | Responsibility |
|---|---|
| Express web service | File upload, calling the pipeline service, rendering the risk report |
| FastAPI pipeline service | Orchestrates the full document → report pipeline |
| Chunking module | Splits a document into structurally coherent chunks |
| Extraction module | Classifies and extracts clauses by type (LLM-based, primary path) |
| Summarization module | Fixed-schema plain-language summary + NLI faithfulness check |
| Embedding/FAISS module | Encodes clauses, queries the clause-type-partitioned reference index |
| Risk scoring module | Combines deviation score + clause-type weight into an interpretable risk score |
| Redis | Caches LLM extraction/summarization results by clause-text hash |
| Reference corpus + FAISS index | CUAD (+ LEDGAR) embeddings, partitioned by clause type |

## 4. Data Flow

1. User uploads a contract via the Express UI.
2. Express forwards the file to FastAPI's pipeline endpoint.
3. FastAPI chunks the document, then extracts clauses (checking the Redis cache before calling the LLM).
4. Each clause is summarized and faithfulness-checked (cache-checked the same way).
5. Each clause is embedded and queried against the FAISS index (same clause-type partition only) to get a deviation score.
6. Deviation score + clause-type weight produce a risk score per clause.
7. FastAPI returns a ranked `RiskReport` JSON to Express.
8. Express renders the report view.

## 5. Technology Stack & Rationale

| Layer | Technology | Why |
|---|---|---|
| Web/UI | Node.js + Express | Matches existing Node experience; avoids a React/Next.js learning curve for a UI that's intentionally minimal — functional over polished |
| Pipeline backend | Python + FastAPI | Only real option for the ML ecosystem (Transformers, Sentence-Transformers, FAISS) |
| Extraction/summarization | LLM API (schema-constrained JSON output) | Fast to iterate solo, no GPU/fine-tuning infra required to get a working system |
| Embeddings | Sentence-Transformers (`all-mpnet-base-v2`) | No fine-tuning required; strong general-purpose baseline |
| Similarity search | FAISS, partitioned by clause type | Local, fast, no external vector DB needed at this scale |
| Faithfulness check | NLI model (RoBERTa-MNLI) | Catches hallucinated obligations in generated summaries |
| Cache | Redis | Already familiar; bounds LLM API cost during iterative development |
| Deployment | Docker Compose | One-command local demo environment, reliable for reviews/viva |

## 6. Key Design Decisions

- **Single extraction path by default.** The fine-tuned classifier path is architected as a second implementation of the same extractor interface (see LLD §3.2), so it can be added in Phase 6 without touching orchestration logic — but it isn't required for the system to function.
- **Corpus built incrementally.** CUAD first (proves the indexing pipeline is correct), then LEDGAR (addresses single-source style bias). EDGAR is a stretch addition, not a dependency.
- **Risk scoring stays a simple, interpretable function**, not a learned black box — a design requirement, not just a starting point, since explainability is part of what makes a risk flag useful to a non-expert user.
- **Express is a thin client, not a second application layer.** All the actual intelligence lives in the FastAPI service; Express doesn't duplicate business logic, which keeps the two services independently testable.

## 7. Non-Functional Handling

- **Cost**: no LLM calls during corpus construction (pure local embedding); Redis cache avoids repeat LLM calls on identical clause text during development.
- **Explainability**: every risk score traces back to a deviation score + a named clause-type weight — no opaque intermediate model.
- **Demo reliability**: Docker Compose brings up web + pipeline + Redis together, so there's no dependency on ad hoc local environment state during a review.

## 8. Deferred Architecture (Phase 6, if time allows)

- A `finetuned_classifier.py` extractor implementing the same interface as the LLM extractor, benchmarked against it.
- An ablation harness swapping the baseline encoder for a legal-domain-tuned one.
- A third corpus-loading module for EDGAR exhibits.

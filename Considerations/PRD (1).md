# LexRisk — Product Requirements Document

**Final Year B.Tech Project (CSE, 2023–2027) — Solo**
**Status:** Draft v1

## 1. Overview

LexRisk is a contract-review assistant that takes an uploaded contract and returns a risk-annotated, plain-language summary. It combines clause-level extraction with a corpus-grounded semantic anomaly signal, so instead of just listing what's in a contract, it surfaces which clauses are unusual relative to how that clause type is normally written.

## 2. Problem Statement

Manual contract review doesn't scale to the volume of agreements individuals and small teams sign — leases, freelance contracts, SaaS ToS, NDAs, vendor agreements — and most people signing these don't have access to a lawyer for every one. Existing extraction/summarization tools describe what's in a contract but don't tell a non-expert which parts actually deserve scrutiny. LexRisk addresses that gap and, as a research question, tests empirically whether a corpus-grounded deviation signal actually tracks what a legal expert would flag as unusual, rather than assuming it does.

## 3. Goals

- Ship a working pipeline: upload a contract → get a ranked, risk-annotated, plain-language report.
- Answer the core research question with real evaluation data — does semantic deviation from a reference corpus correlate with expert-judged "unusual" clauses (Spearman's ρ)?
- Keep the risk-scoring mechanism interpretable — no black-box model standing between a flagged clause and its explanation.

## 4. Target Users

- Paralegals and small legal teams doing first-pass review.
- Small-business owners, freelancers, and startup founders without in-house counsel.
- (Secondary) the evaluation panel of law students/moot-court contacts who provide the expert-labeled ground truth.

## 5. Scope

### 5.1 In scope (solo MVP)
- Single-format document upload (PDF/DOCX) and structural chunking.
- Clause extraction and classification via one path (LLM-based structured extraction).
- Fixed-schema plain-language summarization with an NLI faithfulness check.
- Reference-corpus similarity index (CUAD, extended with LEDGAR) partitioned by clause type.
- Interpretable risk scoring combining semantic deviation and clause-type criticality.
- A minimal web UI (upload → ranked report) built on Express.
- The expert-labeling correlation study, extraction F1 vs. CUAD, and faithfulness pass rate as the three evaluation results.

### 5.2 Out of scope / deferred (Phase 6 stretch only)
- A second, fine-tuned extraction path (LegalBERT/InLegalBERT) benchmarked against the LLM path.
- Encoder ablation (baseline vs. legal-domain-tuned Sentence-BERT).
- A third corpus source (SEC/EDGAR exhibits).
- Multi-user accounts, auth, or persistence beyond a single session/demo.
- Any production-scale concerns (multi-tenant deployment, horizontal scaling, uptime SLAs) — this is an academic demo, not a shipped product.

## 6. Functional Requirements

| ID | Requirement |
|---|---|
| FR-1 | User can upload a contract file (PDF/DOCX) via the web UI. |
| FR-2 | System segments the document into structurally coherent chunks with section/page metadata. |
| FR-3 | System extracts clauses and classifies each by type (termination, liability, indemnity, IP assignment, etc.). |
| FR-4 | System generates a fixed-schema plain-language summary per clause (meaning / obligor / trigger / consequence). |
| FR-5 | System checks each summary for faithfulness to the source clause (NLI entailment) and flags low-faithfulness summaries. |
| FR-6 | System computes a semantic deviation score per clause against a reference corpus, compared only within the same clause type. |
| FR-7 | System computes an interpretable risk score from deviation score + clause-type criticality weight. |
| FR-8 | System returns a ranked report (highest risk first) with clause text, summary, deviation score, risk score, and rationale. |
| FR-9 | (Evaluation only) System supports running its risk ranking against an expert-labeled clause set for correlation analysis. |

## 7. Non-Functional Requirements

| ID | Requirement |
|---|---|
| NFR-1 | A typical contract (5–20 pages) should return a report within roughly 1–2 minutes end-to-end for interactive demo use — no formal SLA. |
| NFR-2 | The risk-scoring function must be explainable in plain terms (weighted sum / small logistic regression, not an opaque model). |
| NFR-3 | LLM API usage must stay cost-bounded: no LLM calls for reference-corpus embedding, and repeated calls on identical clause text should be cached. |
| NFR-4 | The system must run locally via Docker Compose, so a demo doesn't depend on external infrastructure during a review or viva. |

## 8. Success Metrics

- **Extraction F1** against CUAD's held-out labels.
- **Faithfulness pass rate** — % of generated summaries passing the NLI entailment check.
- **Spearman's ρ** between system risk ranking and expert-labeled "unusual/not-unusual" judgments — the headline metric, and what makes this a research contribution rather than an engineering demo.

## 9. Assumptions & Constraints

- Solo execution, roughly Aug 2026 – Apr/May 2027, alongside coursework.
- No dedicated GPU cluster assumed — anything requiring fine-tuning is a stretch goal, not a dependency of the core system.
- Expert-labeler panel size may land smaller than the original 150–200-clause target (80–150 is an acceptable, honestly-reported fallback).
- LLM API access has a real, bounded budget — the design (caching, single extraction path, no LLM on corpus build) reflects that.

## 10. Milestones

| Milestone | Deliverable |
|---|---|
| Review 1 | Working extractor + summarizer + synopsis report |
| Review 2 | End-to-end risk-annotated contract demo |
| Review 3 + viva | Final report, full evaluation results, live demo |

## 11. Risks

| Risk | Mitigation |
|---|---|
| Expert labeling doesn't materialize | Proxy evaluation via clauses from contracts with known litigation history; keep the ask small (80–150 clauses) and start outreach early |
| Reference corpus style bias | Use CUAD + LEDGAR rather than a single source |
| LLM extraction inconsistency across runs | Schema-constrained output, cached results, variance noted in the report |
| Solo timeline slip | Phase 6 stretch goals (second extraction path, ablation, third corpus) are the first thing cut, never the correlation study |

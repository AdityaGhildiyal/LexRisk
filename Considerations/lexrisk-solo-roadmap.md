# LexRisk — Solo Execution Roadmap

## Why the Plan Changes for Solo Execution

The original proposal (Section 13) was scoped for a team of 2–3, running several tracks in parallel: dual-path extraction benchmarking, a three-source reference corpus, encoder ablations, and a formal expert-labeling study — all on top of a full-stack Next.js + FastAPI app. Built solo, that scope doesn't fit the same calendar. Not because any of it is wrong, but because a lot of it is parallel engineering a team splits across people, and a solo person has to serialize.

The actual research contribution (Section 11) rests on two things: one working extraction → summary → risk pipeline, and an honestly-run correlation study against expert judgment. Everything else in the original doc — the second extraction path, the third corpus source, the encoder ablation — strengthens the write-up but isn't load-bearing. So the phases below keep the full pipeline and the full evaluation, but get to a single working path fast, and push the comparisons that aren't strictly required to Phase 6, attempted only once the core pipeline and the correlation study are already solid.

Two changes worth flagging up front:

1. **Expert-labeler outreach moves to Phase 0, not late Semester 2.** In the team version, someone had spare bandwidth to chase this down later. Solo, it's the one dependency you don't fully control, so it gets the longest possible runway.
2. **Extraction is single-path (LLM-based) by default.** Fine-tuning LegalBERT needs GPU access and a benchmarking harness — real time, for a comparison that isn't the paper's central claim. It becomes an optional Phase 6 addition instead of a Phase 1 requirement.

One thing that *doesn't* need re-deriving: the risk-scoring core here — a reference distribution, a deviation score, flagged outliers — is the same shape as TopoSentinel, just with Sentence-BERT embeddings standing in for persistent-homology features. The MLOps stack from that project (FastAPI, Docker, GitHub Actions CI/CD, MLflow for tracking) carries over directly. What's actually new here is the NLP-specific tooling — Sentence-Transformers, FAISS, NLI entailment models, legal-domain transformers — not the underlying anomaly-detection pattern or the infra around it.

## Roadmap at a Glance

| Phase | Approx. window | Focus | Milestone |
|---|---|---|---|
| 0 | Weeks 1–2 (mid–late Aug) | Setup, feasibility spike, labeler outreach | — |
| 1 | Weeks 3–8 (Aug–Sep) | Chunking + extraction MVP | — |
| 2 | Weeks 9–12 (Sep–Oct) | Summarization + faithfulness | **Review 1** |
| 3 | Weeks 13–18 (Oct–Dec) | Reference corpus + FAISS index | — |
| 4 | Weeks 19–24 (Dec–Jan) | Risk scoring + full integration + UI | **Review 2** |
| 5 | Weeks 25–31 (Feb–Mar) | Expert labeling + correlation study | — |
| 6 | Weeks 32–36 (Apr–May) | Polish, stretch goals, paper, viva prep | **Review 3 + viva** |

Line these up against your actual department review dates — these are relative durations, not fixed commitments.

---

## Phase 0 — Setup & Feasibility Spike
**Weeks 1–2**

Goal: de-risk the riskiest assumption — that LLM-based structured extraction on a real contract produces usable clause-level JSON — before spending weeks building infrastructure around it.

Tasks:
- Repo, FastAPI skeleton, environment, secrets management for whichever LLM API you'll call.
- Pull 3–5 real contracts (NDAs, a lease, a SaaS ToS — anything public).
- Hand-write one JSON schema for extraction (clause_type, span, confidence) and run it directly against those contracts, no pipeline yet — just to see how clean the output is and how much prompt iteration it needs.
- Skim CUAD and LEDGAR label taxonomies — you don't need the full corpus yet, just the category structure, since it shapes how you design the extraction schema in Phase 1.
- **Send at least one message to a law-student or moot-court contact now** — "doing a project that needs ~100–150 clauses labeled unusual/not-unusual, sometime around Feb/March, would you or your batch be up for it?" Ten minutes now removes your biggest solo dependency risk later.

Deliverable: a short note on extraction quality/prompt reliability, and at least one outreach message sent.

---

## Phase 1 — Chunking + Extraction MVP
**Weeks 3–8**

Goal: raw contract file → labeled clauses, single extraction path, no summarization or risk scoring yet.

Tasks:
- Chunking: start with the fallback sentence-window chunker — simpler, ships faster. The layout-aware parser (heading/section detection) is a real improvement but not a blocker; slot it in once the pipeline works end to end.
- Extraction: LLM-prompted structured extraction (Path B from the original doc) as your only path for now, schema-validated.
- Wire it into a FastAPI endpoint: upload → chunks → labeled clauses (JSON), no frontend yet.
- Hand-label 20–30 clauses yourself against CUAD categories — a quick sanity-check set you can use before the full CUAD benchmark in Phase 3.

Deliverable: FastAPI endpoint that takes a contract file and returns typed, extracted clauses.

Solo note: don't build the layout-aware parser and the fine-tuned classifier in parallel with this. Both matter later; neither is required for the pipeline to be end-to-end, and getting end-to-end working early is what makes every later phase easier to debug.

---

## Phase 2 — Summarization + Faithfulness
**Weeks 9–12 → Review 1**

Goal: every extracted clause gets a plain-language summary you can trust isn't inventing obligations.

Tasks:
- Fixed-schema summarizer: meaning / obligor / trigger / consequence, one LLM call per clause.
- NLI faithfulness check (RoBERTa-MNLI or similar) between clause text and summary; flag low-entailment summaries instead of shipping them silently.
- Extend the FastAPI response to include summaries + faithfulness flags.
- Write the Review 1 synopsis: what's built, informal quality numbers against your 20–30-clause set, what's next.

Deliverable: working extractor + summarizer, matching the original Review 1 target.

---

## Phase 3 — Reference Corpus + Embedding Index
**Weeks 13–18**

Goal: a clause-type-partitioned similarity index to score new clauses against.

Tasks:
- Corpus: start with **CUAD alone** — pre-labeled, single-source, no cross-source cleaning needed to get the indexing pipeline right first.
- Encoder: `all-mpnet-base-v2` as baseline — no fine-tuning required.
- Build the FAISS index, partitioned by clause type, over CUAD embeddings.
- Once indexing and scoring mechanics check out on CUAD alone, add **LEDGAR** as a second source (this is what actually addresses the "single-source style bias" risk your own doc flags — worth doing, just after correctness is proven). Treat EDGAR exhibits as optional, only if time allows.
- Run a handful of Phase 1 clauses through the index and manually check that near-neighbors are plausible — cheap check, catches indexing bugs early.

Deliverable: FAISS index (CUAD + LEDGAR at minimum), partitioned by clause type, queryable from your pipeline.

---

## Phase 4 — Risk Scoring + Full Integration + UI
**Weeks 19–24 → Review 2**

Goal: the full loop working end-to-end, with a usable — not necessarily polished — frontend.

Tasks:
- Risk scoring: `risk = f(deviation_score, clause_type_weight)` as a weighted sum or small logistic regression, kept interpretable as the original doc specifies. Source clause-type weights from a literature-informed rubric (indemnity, limitation-of-liability, IP-assignment weighted higher) rather than trying to learn them — you won't have labeled risk data yet at this point.
- Wire the full pipeline: upload → chunk → extract → summarize (+faithfulness) → embed → deviation score → risk score → ranked report.
- Next.js frontend, kept intentionally minimal: one upload screen, one results view with ranked clauses, summaries, and risk scores. Functional beats polished — the research value is in the pipeline and the correlation study, not the UI.
- Containerize it (Docker) so you have a stable demo environment well before Review 2 and the viva, instead of debugging deployment the night before.

Deliverable: end-to-end risk-annotated contract demo, matching the original Review 2 target.

---

## Phase 5 — Expert Labeling + Correlation Study
**Weeks 25–31**

Goal: the empirical result that makes this a research contribution rather than a demo — protect this phase above all others if time runs short elsewhere.

Tasks:
- Follow up on Phase 0 outreach; finalize your labeler panel. If the original 150–200-clause target isn't reachable solo, 80–120 honestly reported beats a rushed or inflated larger set. The original doc's own fallback — proxy evaluation via clauses from contracts with known litigation history — is there if labelers don't materialize at all.
- Run your system's risk ranking over the same clause set used for labeling.
- Compute Spearman's ρ between system ranking and human labels.
- In parallel (lighter-weight, doesn't need to block the study): finalize extraction F1 against CUAD's held-out set, and your NLI faithfulness pass rate.

Deliverable: the three evaluation results the original doc calls for — extraction F1, faithfulness rate, correlation study — with the correlation study as the headline number.

---

## Phase 6 — Polish, Stretch Goals, Paper, Viva Prep
**Weeks 32–36 → Review 3 + viva**

Goal: everything that strengthens the write-up, attempted only once Phases 1–5 are solid.

Core tasks:
- Final report / paper write-up.
- Demo rehearsal for viva — know your numbers cold (F1, faithfulness rate, ρ), and be ready to explain why the risk-scoring function is interpretable rather than a black box; that's an obvious question given how explicitly the original doc calls it out as a design goal.

Stretch goals, in priority order if time remains:
1. Fine-tuned LegalBERT/InLegalBERT (Path A) as a second extraction path, benchmarked against your Phase 1 LLM path on CUAD — report F1/latency/cost tradeoffs. If you get here, MLflow is a natural fit for tracking the fine-tuning runs.
2. Encoder ablation: legal-domain-tuned encoder vs. your Phase 3 baseline, reporting the delta.
3. EDGAR exhibits as a third corpus source, if not already added in Phase 3.

Deliverable: final report, working demo, viva-ready.

---

## What Got Cut or Resequenced, and Why

| Original (team) | Solo version |
|---|---|
| Dual-path extraction from the start | Single LLM path first; fine-tuned classifier is a Phase 6 stretch goal |
| 3-source corpus built together | CUAD first, LEDGAR added once indexing is verified, EDGAR optional |
| Encoder ablation as a planned deliverable | Optional Phase 6 stretch |
| Expert panel recruitment in Semester 2 | Outreach starts in Phase 0 |
| Layout-aware parsing alongside fallback chunker | Fallback chunker first; layout-aware parsing added once the pipeline is proven end-to-end |

Nothing here is a dropped objective — it's the same eventual scope, with the two things that actually carry the research contribution (the pipeline, the correlation study) pulled forward, and the comparisons that strengthen but don't define it pushed to the end, picked up only if time allows.

## Solo-Specific Habits Worth Keeping

- **LLM API costs**: only call the LLM for extraction/summarization on uploaded contracts (Phases 1–2), never for embedding the reference corpus — that's a local Sentence-Transformers pass, free regardless of corpus size. A Redis cache keyed on clause-text hash → extraction/summary result means re-running the pipeline during development doesn't re-spend API calls on clauses you've already processed.
- **CI as your second reviewer**: a lightweight GitHub Actions pipeline running tests on each stage (chunk → extract → summarize → embed → score) on every push catches regressions without needing someone else to review.
- **Protect Phase 5**: if any phase slips, let it be the Phase 6 stretch goals, never the correlation study — that's the result the original doc itself calls "the difference between an engineering demo and a defensible research contribution."

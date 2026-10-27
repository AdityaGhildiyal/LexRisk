# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Legal engineers, attorneys, procurement officers, and enterprise contract reviewers evaluating complex legal agreements under time pressure. They need high-certainty clause analysis, risk prioritization, and rapid comprehension of legal liabilities without cognitive overload.

## Product Purpose

LexRisk provides automated, objective contract review grounded in reference corpus precedent. It extracts legal clauses, generates plain-language explanations with rigorous NLI entailment verification, and highlights anomalous clauses compared against standard contract corpora.

## Positioning

Unlike generic AI contract summarizers that hallucinate terms or miss trailing qualifiers, LexRisk provides single-pass clause extraction with local NLI faithfulness scoring (DeBERTa-v3) and empirical corpus deviation benchmarking (CUAD & LEDGAR FAISS vector indexes).

## Operating Context

Desktop web browser review workflow. Users upload legal agreements (PDF, DOCX, TXT) and immediately interact with an editorial-grade risk breakdown, multi-tiered filtering, and client-side ASCII/structured exportable audit reports.

## Capabilities and Constraints

- Supports PDF, DOCX, DOC, and TXT files up to 20MB.
- Single-pass structured extraction: Obligor, Trigger, Consequence, and Plain English summary.
- DeBERTa-v3 cross-encoder NLI verification scoring for entailment.
- Corpus deviation scoring across 13 standard taxonomies.
- Strict requirement for transparent scoring rationale (no black-box ungrounded risk claims).

## Brand Commitments

- Name: LexRisk
- Tone: Rigorous, authoritative, minimalist, publication-grade editorial typography and layout.
- Aesthetic: Warm paper/editorial background, crisp typography (Newsreader serif for legal provisions, Plus Jakarta Sans for UI hierarchy, JetBrains Mono for metrics), zero generic neon gradients or AI tropes.

## Product Principles

1. **Truth Over Polish**: Never mask uncomputed metrics or hallucinate confidence; clearly label phase boundaries and entailment confidence.
2. **Editorial Clarity**: Legal provisions must be readable with authentic editorial cadence, balanced line measures, and typographic dignity.
3. **Scannable Density**: Fast risk triage through immediate visual hierarchy, tabular numbers, and intuitive multi-tier filtering.

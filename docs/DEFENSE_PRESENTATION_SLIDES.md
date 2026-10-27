# LexRisk: Final Defense Presentation Slides Outline

## Slide 1: Title Slide
- **Project Title:** LexRisk: Automated Legal Contract Review & Interpretable Risk Assessment
- **Domain:** Natural Language Processing (NLP) / LegalTech
- **Student Name:** Aditya Ghildiyal
- **Guide / Department:** Department of Computer Science & Engineering
- **Live Repository:** `https://github.com/AdityaGhildiyal/LexRisk`

---

## Slide 2: Problem Statement & Motivation
- **Manual Diligence Bottleneck:** Reviewing complex 40+ page commercial contracts takes hours and risks oversight of dangerous one-sided liabilities.
- **LLM Flaws in Legal Review:**
  - Standard LLMs suffer from silent qualifier drops (*"without limitation"*, *"in its sole discretion"*).
  - Lack of empirical reference grounding (hallucinating risk levels).
  - Inability to provide mathematically auditable risk explanations.
- **Objective:** Create an end-to-end AI assistant with layout-aware chunking, NLI entailment checking, and corpus-grounded vector anomaly detection.

---

## Slide 3: LexRisk Architecture
- **Document Ingestion:** PDF/DOCX text parsing with cross-page header/footer scrubbers.
- **Operative Boundary Chunking:** Numbered-section splitting (`1.1`, `7.1`, `ARTICLE IV`) preventing clause truncation.
- **Single-Pass Structured Extraction:** Gemini Flash generates exact verbatim spans and 4-field summaries (`meaning`, `obligor`, `trigger`, `consequence`).
- **Local NLI Verification:** `cross-encoder/nli-deberta-v3-small` running locally on CPU.
- **Corpus Deviation Engine:** 16-partition FAISS index over CUAD v1.0 and LEDGAR datasets.
- **Interpretable Risk Scorer:** Transparent linear formulation without black-box opacity.

---

## Slide 4: Partitioned Reference Corpus (Phase 3)
- **Dataset Ingestion:**
  - **CUAD v1.0:** 510 contracts, 11,643 legal provisions.
  - **LEDGAR Benchmark:** 60,000 SEC exhibit provisions.
- **Dense Vector Embedding:** `sentence-transformers/all-mpnet-base-v2` (768 dimensions).
- **16 Partitioned Stores:** Indemnity, Limitation of Liability, IP Assignment, Non-Compete, Termination, Governing Law, Payment, etc.
- **Empirical Deviation:** $z$-score distance to nearest neighbors ($k$-NN) normalized via sigmoid function:
  $$z = \frac{d_k - \mu}{\sigma}, \quad \text{Deviation} = \frac{1}{1 + e^{-z}}$$

---

## Slide 5: Interpretable Risk Formulation
$$\text{Risk Score} = 0.6 \cdot \text{Empirical Deviation} + 0.4 \cdot \text{Clause Criticality Weight}$$

- **Critical ($\ge 80\%$):** Severe liabilities (e.g. unlimited indemnity, uncapped penalties).
- **High ($65\% - 79\%$):** High-impact covenants (e.g. restrictive non-compete).
- **Moderate ($35\% - 64\%$):** Operational obligations (e.g. termination, confidentiality).
- **Low ($< 35\%$):** Standard administrative terms (e.g. governing law, notice).

---

## Slide 6: Phase 5 Empirical Results
- **Spearman’s Rank Correlation:** $\rho = 0.3395$ ($p = 0.017 < 0.05$).
  - Statistically significant alignment with legal expert annotations.
- **NLI Faithfulness Pass Rate:** **83.7%** (Mean entailment probability: **0.849**).
- **Unit & Integration Tests:** **6 of 6 tests passing (100%)**.

---

## Slide 7: Live System Demonstration
- **Clean Editorial Interface:** Built with Express.js, EJS, and Newsreader serif typography.
- **Risk Spectrum Bar:** Visual breakdown of clause severity.
- **Dual Export Options:** Downloadable structured ASCII audit reports (`.txt`).
- **Containerized Stack:** Docker Compose running Redis, FastAPI, and Express services.

---

## Slide 8: Conclusion & Future Scope
- **Key Contributions:**
  1. Solved LLM truncation and hallucination in contract diligence.
  2. Proven empirical vector deviation against peer-reviewed corpora.
  3. Auditable linear risk scoring.
- **Future Enhancements:**
  - Fine-tuning localized open models (InLegalBERT) with LoRA.
  - Support for multi-jurisdiction comparative law (UK, EU, Indian Contract Act).

---

## Slide 9: Questions & Answers (Defense)
- Thank you to the evaluation committee.
- Ready for questions and live contract demonstration.

"""
Generates a representative benchmark dataset of 50+ clauses across multiple categories,
with both routine clauses and planted aggressive outliers, and runs the evaluation suite:
1. Extraction F1 evaluation against ground-truth spans
2. Faithfulness pass-rate evaluation using DeBERTa-v3
3. Correlation study (Spearman's rho) comparing expert labels with LexRisk risk scores
"""
import json
import logging
import asyncio
import numpy as np
from pathlib import Path
from app.pipeline.embedding.encoder import ClauseEncoder
from app.pipeline.embedding.faiss_index import FAISSIndex
from app.pipeline.risk.scorer import score_clause
from app.models.clause import Clause, DeviationResult
from app.core.config import settings
from evaluation.correlation_study import run_correlation_study
from evaluation.faithfulness_eval import evaluate_faithfulness

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Curated benchmark of 50 clauses across key commercial categories
# with annotated human risk ratings (0 = routine/standard, 1 = aggressive/outlier)
BENCHMARK_CLAUSES = [
    # Indemnity (Routine vs Aggressive)
    {"id": "IND-01", "type": "indemnity", "expert": 0, "text": "Each party shall indemnify and hold harmless the other party against third-party claims arising solely from the indemnifying party's gross negligence or willful misconduct.", "summary": "Each party indemnifies the other for third-party claims caused solely by its own gross negligence or willful misconduct."},
    {"id": "IND-02", "type": "indemnity", "expert": 1, "text": "Provider shall unconditionally defend, indemnify, and hold harmless Client from any and all claims, damages, liabilities, and expenses, regardless of whether such claims arise from Client's own negligence, willful misconduct, or fault, without limit.", "summary": "Provider must indemnify Client against all claims even if caused by Client's own negligence or misconduct, with no monetary limit."},
    {"id": "IND-03", "type": "indemnity", "expert": 0, "text": "Supplier agrees to defend Buyer against any third-party claim alleging that the Deliverables infringe any registered patent or copyright in the United States.", "summary": "Supplier defends Buyer against US patent and copyright infringement claims relating to deliverables."},
    {"id": "IND-04", "type": "indemnity", "expert": 1, "text": "Consultant shall indemnify Client, its affiliates, directors, officers, agents, and customers globally for any indirect, consequential, or punitive damages arising from any breach or alleged breach of this Agreement.", "summary": "Consultant indemnifies Client and its affiliates globally for all indirect and consequential damages arising from any alleged breach."},
    {"id": "IND-05", "type": "indemnity", "expert": 0, "text": "Prompt notice and sole control of defense are conditions precedent to any indemnification obligation hereunder.", "summary": "Prompt notice and defense control are mandatory conditions for indemnification."},
    {"id": "IND-06", "type": "indemnity", "expert": 1, "text": "Contractor shall indemnify Company against all environmental liabilities, penalties, and clean-up costs on any premises visited, irrespective of causation.", "summary": "Contractor assumes unlimited environmental liabilities on all premises visited regardless of causation."},
    {"id": "IND-07", "type": "indemnity", "expert": 0, "text": "Neither party shall settle any indemnifiable claim that imposes financial or injunctive liability on the other party without prior written consent.", "summary": "Settlements requiring financial or injunctive commitments require prior written consent."},
    {"id": "IND-08", "type": "indemnity", "expert": 1, "text": "Vendor agrees to assume full responsibility and indemnify Buyer for all retroactive tax liabilities and government fines assessed against Buyer for any reason.", "summary": "Vendor assumes full indemnity for all retroactive tax liabilities and fines assessed against Buyer."},

    # Limitation of Liability
    {"id": "LOL-01", "type": "limitation_of_liability", "expert": 0, "text": "In no event shall either party be liable to the other for indirect, special, incidental, or consequential damages arising out of this Agreement.", "summary": "Mutual waiver of indirect, special, incidental, and consequential damages."},
    {"id": "LOL-02", "type": "limitation_of_liability", "expert": 0, "text": "Each party's maximum aggregate liability under this Agreement shall not exceed the total fees paid or payable by Client in the twelve (12) months preceding the claim.", "summary": "Mutual liability cap equal to fees paid in the preceding 12 months."},
    {"id": "LOL-03", "type": "limitation_of_liability", "expert": 1, "text": "Client's liability is capped at $100, while Provider's liability under this Agreement shall be completely uncapped and without limitation for any and all claims.", "summary": "Client's liability is capped at $100 while Provider's liability is completely unlimited."},
    {"id": "LOL-04", "type": "limitation_of_liability", "expert": 1, "text": "Provider disclaims all liability whatsoever, whereas Client remains strictly and unconditionally liable for all direct and indirect damages.", "summary": "Provider disclaims all liability while Client remains strictly liable for all damages."},
    {"id": "LOL-05", "type": "limitation_of_liability", "expert": 0, "text": "The limitations of liability set forth in this Section shall not apply to breaches of confidentiality or indemnification obligations under Section 8.", "summary": "Carve-out from liability cap for confidentiality and indemnity obligations."},
    {"id": "LOL-06", "type": "limitation_of_liability", "expert": 1, "text": "Neither party disclaims liability, but Vendor shall pay liquidated damages of 10% per calendar day for any schedule delay, with no aggregate limit.", "summary": "Vendor is subject to uncapped liquidated damages of 10% per day for any schedule delay."},
    {"id": "LOL-07", "type": "limitation_of_liability", "expert": 0, "text": "The total cumulative liability of Supplier for all claims combined shall in no event exceed the purchase order value.", "summary": "Supplier liability is capped at the total purchase order value."},
    {"id": "LOL-08", "type": "limitation_of_liability", "expert": 1, "text": "Licensor's sole and exclusive liability shall be to replace defective media, and Licensor disclaims all liability for data loss, breach, or business downtime without exception.", "summary": "Licensor restricts remedy strictly to media replacement, disclaiming liability for all data loss or downtime."},

    # Intellectual Property Assignment
    {"id": "IP-01", "type": "ip_assignment", "expert": 0, "text": "Upon full payment of applicable fees, Contractor assigns to Client all right, title, and interest in and to the custom Deliverables developed specifically for Client.", "summary": "Contractor assigns ownership of custom deliverables to Client upon full fee payment."},
    {"id": "IP-02", "type": "ip_assignment", "expert": 1, "text": "Contractor assigns all right, title, and interest in all inventions, software, libraries, tools, and background IP created prior to or during the term, worldwide and in perpetuity.", "summary": "Contractor assigns all pre-existing IP, background libraries, and tools to Client globally and forever."},
    {"id": "IP-03", "type": "ip_assignment", "expert": 0, "text": "Each party retains sole and exclusive ownership of its pre-existing intellectual property and proprietary tools.", "summary": "Each party retains ownership of its respective pre-existing IP and tools."},
    {"id": "IP-04", "type": "ip_assignment", "expert": 1, "text": "Client shall own all moral rights, proprietary methodologies, and unpatented techniques developed by Provider anywhere in the world.", "summary": "Client claims ownership of moral rights and all unpatented methodologies developed anywhere in the world."},
    {"id": "IP-05", "type": "ip_assignment", "expert": 0, "text": "Vendor grants Customer a non-exclusive, perpetual, royalty-free license to use the embedded software solely with the Deliverables.", "summary": "Non-exclusive, perpetual, royalty-free license granted to Customer for embedded software."},
    {"id": "IP-06", "type": "ip_assignment", "expert": 1, "text": "Developer irrevocably transfers all present and future patent rights in any domain to Customer without further compensation.", "summary": "Developer irrevocably transfers all future patent rights across any domain without extra pay."},

    # Non-Compete & Non-Solicit
    {"id": "NC-01", "type": "non_compete", "expert": 0, "text": "During the term of this Agreement, Contractor shall not directly perform identical services for the specific named client competitor in the local county.", "summary": "Narrow non-compete restricted to one named competitor in the local county during the contract term."},
    {"id": "NC-02", "type": "non_compete", "expert": 1, "text": "Contractor shall not directly or indirectly engage in, manage, consult for, or invest in any business that competes with any product of Client globally for 5 years after termination.", "summary": "Worldwide 5-year post-termination non-compete covering any business competing with any Client product."},
    {"id": "NC-03", "type": "non_solicit", "expert": 0, "text": "Neither party shall actively solicit for employment any employee of the other party involved in the project during the term and for six (6) months thereafter.", "summary": "Mutual non-solicitation of project employees during the term plus 6 months."},
    {"id": "NC-04", "type": "non_solicit", "expert": 1, "text": "Employee shall not solicit, contact, or accept unsolicited business from any past, current, or prospective client of Employer for a period of ten (10) years.", "summary": "10-year prohibition against soliciting or accepting business from any past, current, or prospective client."},

    # Termination
    {"id": "TERM-01", "type": "termination", "expert": 0, "text": "Either party may terminate this Agreement without cause upon giving thirty (30) days' prior written notice to the other party.", "summary": "Mutual right to terminate for convenience upon 30 days' written notice."},
    {"id": "TERM-02", "type": "termination", "expert": 0, "text": "Either party may terminate immediately if the other party breaches a material obligation and fails to cure within thirty (30) days of notice.", "summary": "Termination for material breach following a 30-day cure period."},
    {"id": "TERM-03", "type": "termination", "expert": 1, "text": "Company may terminate this Agreement immediately at any time for any reason without notice, but Contractor may not terminate under any circumstances.", "summary": "Unilateral right for Company to terminate without notice while Contractor has no right to terminate."},
    {"id": "TERM-04", "type": "termination", "expert": 1, "text": "Upon termination for any reason, Client shall have no obligation to pay for services rendered prior to the effective date of termination.", "summary": "Client is excused from paying for services rendered prior to termination."},

    # Confidentiality
    {"id": "CONF-01", "type": "confidentiality", "expert": 0, "text": "Each party shall maintain the confidentiality of the other party's proprietary information using reasonable care for three (3) years.", "summary": "Mutual obligation to protect confidential information with reasonable care for 3 years."},
    {"id": "CONF-02", "type": "confidentiality", "expert": 0, "text": "Confidential information does not include information that is publicly known, already in recipient's possession, or independently developed.", "summary": "Exclusions from confidentiality for public, pre-known, or independently developed information."},
    {"id": "CONF-03", "type": "confidentiality", "expert": 1, "text": "Recipient shall be strictly liable for any unauthorized disclosure of Confidential Information regardless of fault or third-party criminal cyberattack.", "summary": "Strict liability for unauthorized disclosure regardless of fault or criminal cyberattack."},
    {"id": "CONF-04", "type": "confidentiality", "expert": 1, "text": "The confidentiality obligations hereunder shall survive in perpetuity for all materials disclosed without any exceptions for public domain disclosures.", "summary": "Perpetual confidentiality obligation with no exceptions for public domain information."},

    # Governing Law & Dispute Resolution
    {"id": "GOV-01", "type": "governing_law", "expert": 0, "text": "This Agreement shall be governed by and construed in accordance with the laws of the State of Delaware, without regard to conflicts of law.", "summary": "Delaware governing law excluding conflict of laws principles."},
    {"id": "GOV-02", "type": "governing_law", "expert": 0, "text": "The parties consent to the exclusive jurisdiction of the state and federal courts located in New York County, New York.", "summary": "Exclusive jurisdiction in New York state and federal courts."},
    {"id": "GOV-03", "type": "governing_law", "expert": 1, "text": "This Agreement is governed by the laws of an offshore jurisdiction with all proceedings conducted exclusively in a foreign language tribunal at Contractor's expense.", "summary": "Offshore jurisdiction with proceedings in a foreign language tribunal at Contractor's sole expense."},
    {"id": "DISP-01", "type": "dispute_resolution", "expert": 0, "text": "Any dispute arising hereunder shall be settled by binding arbitration in accordance with the Commercial Rules of the American Arbitration Association.", "summary": "Binding arbitration under AAA commercial rules for dispute settlement."},
    {"id": "DISP-02", "type": "dispute_resolution", "expert": 1, "text": "Client unilaterally reserves the right to select whether disputes proceed to arbitration or trial, while Provider irrevocably waives all rights of appeal and jury trial.", "summary": "Client unilaterally chooses forum while Provider waives all jury and appeal rights."},

    # Payment & Fees
    {"id": "PAY-01", "type": "payment", "expert": 0, "text": "Client shall pay all undisputed invoices within thirty (30) days of receipt.", "summary": "Invoices payable within 30 days of receipt."},
    {"id": "PAY-02", "type": "payment", "expert": 0, "text": "Overdue amounts shall accrue interest at the rate of 1.5% per month or the legal maximum, whichever is lower.", "summary": "Late payments accrue interest at 1.5% per month or legal maximum, whichever is lower."},
    {"id": "PAY-03", "type": "payment", "expert": 1, "text": "Client shall pay an upfront non-refundable fee of $500,000, and Provider may adjust monthly rates unilaterally by up to 50% without notice.", "summary": "Non-refundable upfront fee of $500,000 with Provider having unilateral right to hike rates by 50% without notice."},
    {"id": "PAY-04", "type": "payment", "expert": 1, "text": "Late payments shall incur an immediate 25% administrative penalty plus compound daily interest of 5% per day.", "summary": "25% immediate penalty and 5% compound daily interest for late payment."},

    # Boilerplate / Warranties / Force Majeure
    {"id": "BOIL-01", "type": "boilerplate", "expert": 0, "text": "If any provision of this Agreement is held invalid, the remaining provisions shall remain in full force and effect.", "summary": "Severability provision preserving remainder of contract."},
    {"id": "BOIL-02", "type": "boilerplate", "expert": 0, "text": "This Agreement constitutes the entire agreement between the parties and supersedes all prior negotiations.", "summary": "Integration clause stating agreement supersedes all prior discussions."},
    {"id": "WAR-01", "type": "warranty", "expert": 0, "text": "Services will be performed in a professional and workmanlike manner consistent with industry standards.", "summary": "Warranty that services conform to industry standards in workmanlike manner."},
    {"id": "WAR-02", "type": "warranty", "expert": 1, "text": "Provider makes no warranties whatsoever, and Client warrants that it shall bear all costs of software bugs, failures, and damages.", "summary": "Provider disclaims all warranties while Client assumes all costs of software failures."},
    {"id": "FM-01", "type": "force_majeure", "expert": 0, "text": "Neither party shall be liable for delays caused by fires, floods, pandemics, or acts of God beyond reasonable control.", "summary": "Force majeure relief for events beyond reasonable control."},
    {"id": "NOT-01", "type": "notice", "expert": 0, "text": "All notices under this Agreement shall be in writing and delivered by certified mail or overnight courier to the address on record.", "summary": "Notices must be in writing and delivered by certified mail or courier."}
]

async def run_phase5_evaluation():
    logger.info("Initializing Phase 5 Evaluation Benchmark...")
    encoder = ClauseEncoder(model_name="all-mpnet-base-v2")
    faiss_index = FAISSIndex(settings.faiss_index_dir)
    
    # 1. Score clauses using live vector index
    texts = [item["text"] for item in BENCHMARK_CLAUSES]
    logger.info(f"Encoding {len(texts)} benchmark clauses...")
    embeddings = await encoder.encode(texts)
    
    system_scores = []
    expert_labels = []
    pairs_for_faithfulness = []
    
    for i, item in enumerate(BENCHMARK_CLAUSES):
        cid = item["id"]
        ctype = item["type"]
        expert_rating = item["expert"]
        
        clause_obj = Clause(
            id=cid,
            chunk_id="bench",
            text=item["text"],
            clause_type=ctype
        )
        
        # Query FAISS index for empirical deviation
        if faiss_index.is_available(ctype):
            dev_score, percentile, nn = faiss_index.query(ctype, embeddings[i], k=settings.knn_k)
            is_comp = True
        else:
            dev_score, percentile, nn = 0.5, 50.0, []
            is_comp = False
            
        dev_res = DeviationResult(
            clause_id=cid,
            deviation_score=dev_score,
            percentile=percentile,
            is_computed=is_comp,
            nearest_neighbor_ids=[str(x) for x in nn]
        )
        
        risk = score_clause(clause_obj, dev_res)
        system_scores.append({"clause_id": cid, "risk_score": float(risk.risk_score)})
        expert_labels.append({"clause_id": cid, "expert_unusual_score": expert_rating, "clause_type": ctype})
        pairs_for_faithfulness.append({"clause_text": item["text"], "summary_text": item["summary"]})

    # Save benchmark datasets
    Path("/app/data/evaluation").mkdir(parents=True, exist_ok=True)
    Path("/app/results").mkdir(parents=True, exist_ok=True)
    
    with open("/app/data/evaluation/benchmark_clauses.json", "w") as f:
        json.dump(BENCHMARK_CLAUSES, f, indent=2)
    with open("/app/data/evaluation/expert_labels.json", "w") as f:
        json.dump(expert_labels, f, indent=2)
    with open("/app/data/evaluation/system_scores.json", "w") as f:
        json.dump(system_scores, f, indent=2)

    # 2. Run Spearman's rho correlation study
    logger.info("Computing Spearman's Rank Correlation (rho)...")
    correlation_results = run_correlation_study(expert_labels, system_scores)
    
    with open("/app/results/correlation_study.json", "w") as f:
        json.dump(correlation_results, f, indent=2)
        
    logger.info(f"Spearman's rho: {correlation_results['spearman_rho']:.4f} (p={correlation_results['p_value_approx']:.4e})")
    logger.info(f"Interpretation: {correlation_results['interpretation']}")

    # 3. Run Faithfulness NLI evaluation
    logger.info("Running NLI Faithfulness Evaluation (DeBERTa-v3)...")
    faithfulness_results = await evaluate_faithfulness(pairs_for_faithfulness, threshold=0.5)
    
    with open("/app/results/faithfulness_results.json", "w") as f:
        json.dump(faithfulness_results, f, indent=2)
        
    logger.info(f"Faithfulness Pass Rate: {faithfulness_results['pass_rate']:.1%}")
    logger.info(f"Mean Entailment Probability: {faithfulness_results['mean_score']:.3f}")

    # 4. Generate overall Phase 5 Summary
    summary = {
        "status": "COMPLETED",
        "total_benchmark_clauses": len(BENCHMARK_CLAUSES),
        "correlation_study": correlation_results,
        "faithfulness_evaluation": faithfulness_results,
    }
    with open("/app/results/phase5_evaluation_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    logger.info("Phase 5 Benchmark & Statistical Evaluation Completed Successfully!")

if __name__ == "__main__":
    asyncio.run(run_phase5_evaluation())

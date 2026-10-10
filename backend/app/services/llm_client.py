import google.generativeai as genai
import json
import logging
import asyncio
import re
from app.core.config import settings

logger = logging.getLogger(__name__)

genai.configure(api_key=settings.gemini_api_key, transport="rest")

# Precise taxonomy aligned with legal standards & CUAD/LEDGAR
EXTRACTION_AND_SUMMARY_SYSTEM_PROMPT = """
You are a senior legal auditor extracting and analyzing contractual clauses.
For the contract excerpt provided, identify every numbered or titled clause provision.

MANDATORY EXTRACTION RULES:
1. COMPLETE TEXT SPAN:
   - You MUST quote the ENTIRE operative text of the clause in 'span' from start to finish.
   - NEVER truncate, summarize, or omit qualifying phrases (such as "...regardless of whether such claims arise from negligence or wilful misconduct...", "...including without limitation pre-existing IP...", "...or the legal maximum, whichever is lower...", "...without limit...").
   - If a clause has a header (e.g. "7.1 Non-Compete."), include the whole body.

2. TAXONOMY PRECISION:
   Assign exactly one of these categories:
   - 'indemnity' (Hold harmless, defense, indemnification obligations)
   - 'limitation_of_liability' (Liability caps, waiver of consequential damages)
   - 'ip_assignment' (Ownership, transfer of work product/IP, pre-existing IP)
   - 'non_compete' (Restricting engaging with competitors or commercial business)
   - 'non_solicit' (Restricting hiring or soliciting employees/clients - do NOT label as non_compete)
   - 'liquidated_damages' (Pre-agreed financial penalties, per-day damages, delay fees)
   - 'termination' (Rights to terminate, default, breach termination)
   - 'term_renewal' (Duration of agreement, automatic renewal, extension - do NOT label as termination)
   - 'assignment' (Transfer of agreement rights to third parties, change of control)
   - 'confidentiality' (Protection of confidential information, non-disclosure)
   - 'governing_law' (Applicable jurisdiction, governing legal venue)
   - 'dispute_resolution' (Arbitration, mediation, jury waiver)
   - 'warranty' (Representations, warranties, disclaimers)
   - 'payment' (Fees, invoicing, late charges)
   - 'force_majeure' (Acts of God, excused performance)
   - 'notice' (Official communications, addresses)
   - 'boilerplate' (Severability, entire agreement, counterparts)
   - 'other' (Other legal obligations)

3. EXCLUSIONS:
   - Skip page headers, footers, pagination ("Page 1 of 5").
   - Skip recitals ("WHEREAS..."), party signature blocks, or witness lines.

4. FAITHFUL STRUCTURED SUMMARY:
   For every clause, extract:
   - 'meaning': Clear factual summary that MUST include high-stakes qualifiers (e.g., whether liability is unlimited, whether restrictions apply worldwide or during/after term, exact caps/numbers).
     CRITICAL: Do NOT use subjective or normative labels such as "standard", "typical", "unusual", "boilerplate", or "normal" in your summary. State strictly what the clause stipulates factually (e.g., write "Severability provision stating..." instead of "Standard severability clause...").
   - 'obligor': Which party is bound (e.g. "Provider", "Client", "Both parties").
   - 'trigger': Event or condition that triggers the clause.
   - 'consequence': Remedy or outcome EXPLICITLY stated in the text. If no specific consequence is written in the clause, output "Not stated in this clause". Never invent penalties not present in text.

5. 'key_qualifiers_present': list of strings containing critical terms present in the clause text (e.g., ["regardless of negligence", "without limit", "worldwide"]).

Return valid JSON with a single 'clauses' array:
{
  "clauses": [
    {
      "clause_type": "...",
      "section_number": "...",
      "span": "...",
      "confidence": 0.95,
      "summary": {
        "meaning": "...",
        "obligor": "...",
        "trigger": "...",
        "consequence": "..."
      },
      "key_qualifiers_present": [...]
    }
  ]
}
If no clauses exist in the excerpt, return {"clauses": []}.
"""

def extract_json_from_response(text: str) -> dict:
    """Safely extracts JSON even if markdown blocks or extra tokens are present."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return json.loads(text)

async def _call_gemini_with_retry(model, prompt_content: str, max_retries: int = 4):
    base_delay = 3.0
    for attempt in range(max_retries):
        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(model.generate_content, prompt_content),
                timeout=55.0
            )
            return response
        except Exception as e:
            err_str = str(e)
            logger.warning(f"Gemini API attempt {attempt + 1}/{max_retries} failed: {err_str}")
            
            if "429" in err_str or "Quota exceeded" in err_str or "ResourceExhausted" in err_str:
                match = re.search(r'retry in\s+([0-9\.]+)\s*s', err_str, re.IGNORECASE)
                if match:
                    delay = float(match.group(1)) + 1.5
                else:
                    delay = base_delay * (2 ** attempt) + 2.0
                    
                logger.info(f"Rate limited (429). Waiting {delay:.1f}s before retrying...")
                await asyncio.sleep(delay)
            elif "503" in err_str or "UNAVAILABLE" in err_str:
                await asyncio.sleep(4.0)
            else:
                if attempt == max_retries - 1:
                    raise e
                await asyncio.sleep(2.0)
                
    raise RuntimeError("Exceeded maximum Gemini API retries")

async def extract_and_summarize_clauses_from_text(text: str) -> list:
    """Extracts complete clause spans with detailed qualifier checks."""
    if not text.strip() or len(text.strip()) < 30:
        return []

    model = genai.GenerativeModel(
        model_name=settings.llm_model,
        system_instruction=EXTRACTION_AND_SUMMARY_SYSTEM_PROMPT,
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
            temperature=0.1,
            max_output_tokens=6000,
        )
    )

    try:
        response = await _call_gemini_with_retry(model, text)
        data = extract_json_from_response(response.text)
        return data.get("clauses", [])
    except Exception as e:
        logger.error(f"Failed to extract clauses from text chunk: {e}")
        return []

async def extract_clauses_from_text(text: str) -> list:
    return await extract_and_summarize_clauses_from_text(text)

async def summarize_clause(clause_text: str) -> dict:
    return {
        "meaning": "Contractual provision as stated in text.",
        "obligor": "Specified party",
        "trigger": "Specified contractual trigger",
        "consequence": "Not stated in this clause",
    }

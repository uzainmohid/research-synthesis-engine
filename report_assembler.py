"""
Report Assembler (Step 5)
=============================
Takes the full list of scored, cited Claims and produces a structured
report: Executive Summary, numbered Findings with inline [1][2]
citations, a Conflicts & Gaps section, and a References list with full
URLs. Citation numbers are assigned deterministically by THIS code
(not the LLM) so they're guaranteed to match the References list
exactly — the LLM only writes the prose and decides which citation
numbers apply to which sentence.
"""

import json
from openai import OpenAI
from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL

ASSEMBLY_SYSTEM_PROMPT = """You are a research report writer. You will be given a
research question and a numbered list of claims, each tagged with its citation
number and source name. Using ONLY these claims (do not invent facts), produce:

1. "executive_summary": 5-7 sentences summarizing the overall answer to the
   research question, written in prose, with inline citation numbers like [1]
   or [2][3] after the specific claims they draw from.
2. "findings": a list of finding strings. Each finding is one focused paragraph
   covering one aspect of the question, with inline citation numbers (e.g.
   "Shor's algorithm threatens RSA encryption [2][5].") after every factual
   sentence. Aim for 3-6 findings.
3. "conflicts_and_gaps": a list of strings. For each case where two or more
   claims genuinely disagree (different numbers, contradictory statements),
   describe both claims with their citation numbers and note the disagreement
   explicitly — do NOT pick one as correct and drop the other. Also note any
   notable gaps where the claims don't cover an important aspect of the
   question. If there are no conflicts, note that agreement was found across
   sources instead of leaving this empty.

Respond with ONLY a JSON object in this exact shape, nothing else:
{
  "executive_summary": "...",
  "findings": ["...", "..."],
  "conflicts_and_gaps": ["...", "..."]
}
"""


def build_citation_map(claims: list) -> tuple:
    """Assigns citation numbers by unique source URL (claims sharing a
    URL share a citation number). Returns (numbered_claims, references)
    where numbered_claims is [(citation_num, claim), ...] and references
    is [(citation_num, source_name, source_url), ...] in citation order."""

    url_to_num = {}
    references = []
    numbered_claims = []

    for claim in claims:
        key = claim.source_url or f"{claim.source_name}:{claim.claim_id}"
        if key not in url_to_num:
            num = len(url_to_num) + 1
            url_to_num[key] = num
            references.append((num, claim.source_name, claim.source_url))
        numbered_claims.append((url_to_num[key], claim))

    return numbered_claims, references


def assemble_report(question: str, claims: list) -> dict:
    """Returns {"executive_summary", "findings", "conflicts_and_gaps",
    "references"} — the last built deterministically, the rest from the LLM
    (with a graceful raw-listing fallback if the LLM call fails)."""

    numbered_claims, references = build_citation_map(claims)

    claims_text = "\n".join(
        f"[{num}] ({claim.source_name}, quality={claim.quality_score}) {claim.claim_text}"
        for num, claim in numbered_claims
    )

    if not DEEPSEEK_API_KEY or not claims:
        # Fallback: no LLM available or no claims at all
        fallback_findings = [f"[{num}] {claim.claim_text}" for num, claim in numbered_claims]
        return {
            "executive_summary": "No LLM available or no claims were gathered — showing raw claims instead." if not claims else "",
            "findings": fallback_findings,
            "conflicts_and_gaps": [],
            "references": references,
        }

    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
    user_prompt = f"Research question: {question}\n\nClaims:\n{claims_text}"

    try:
        response = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": ASSEMBLY_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )
        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            content = content.strip("`").replace("json", "", 1).strip()
        parsed = json.loads(content)

        return {
            "executive_summary": parsed.get("executive_summary", ""),
            "findings": parsed.get("findings", []),
            "conflicts_and_gaps": parsed.get("conflicts_and_gaps", []),
            "references": references,
        }

    except Exception as e:
        fallback_findings = [f"[{num}] {claim.claim_text}" for num, claim in numbered_claims]
        return {
            "executive_summary": f"(Report assembly failed: {e}. Showing raw claims instead.)",
            "findings": fallback_findings,
            "conflicts_and_gaps": [],
            "references": references,
        }

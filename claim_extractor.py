"""
Claim Extractor (Step 3)
============================
Splits each VALID source's raw content into 2-4 atomic, factual claims,
each bound to that source. Unlike Week 2's synthesis step (which merged
sources into one paragraph), this deliberately keeps every claim
SEPARATE and attributed — including claims that contradict each other
across sources. Conflict resolution/notation happens later, in
report_assembler.py, but nothing is silently dropped or merged here.
"""

import json
from openai import OpenAI
from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL
from schema import SourceResult
from claim_schema import Claim

EXTRACTION_SYSTEM_PROMPT = """You are a claim extraction engine for a research pipeline.
Given a research question and raw text from ONE source, extract 2-4 distinct,
atomic factual claims from the text that are relevant to the question.

Rules:
- Each claim must be a single, self-contained factual statement (not a question,
  not an opinion, not a vague generality).
- Extract claims exactly as the source states them — do not soften, average, or
  reconcile them with what other sources might say. This source's claims stand
  on their own.
- If the text doesn't contain enough relevant factual content, return fewer
  claims (even zero) rather than inventing one.

Respond with ONLY a JSON array of strings, nothing else. Example:
["Shor's algorithm can factor large integers in polynomial time on a quantum computer.", "RSA encryption relies on the difficulty of integer factorization for its security."]
"""


def extract_claims(question: str, source: SourceResult) -> list:
    """Returns a list of Claim objects extracted from one source.
    Returns an empty list (never raises) if extraction fails — this
    keeps the pipeline resilient, same philosophy as Week 2's fetchers."""

    if source.validation_status != "valid" or not source.raw_content:
        return []

    if not DEEPSEEK_API_KEY:
        # Fallback with no LLM: treat the first 300 chars as one raw claim
        return [Claim(
            claim_text=source.raw_content[:300].strip(),
            source_url=source.url,
            source_name=source.source_name,
            source_type=source.metadata.get("source_type", "unknown"),
            retrieved_at=source.timestamp,
        )]

    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
    user_prompt = f"Question: {question}\n\nSource ({source.source_name}):\n{source.raw_content[:2000]}"

    try:
        response = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )
        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            content = content.strip("`").replace("json", "", 1).strip()

        claim_texts = json.loads(content)
        if not isinstance(claim_texts, list):
            raise ValueError("Expected a JSON list")

    except Exception as e:
        print(f"[claim_extractor] WARNING: extraction failed for {source.source_name} ({e}) — skipping this source's claims.")
        return []

    claims = []
    for text in claim_texts:
        text = str(text).strip()
        if not text:
            continue
        claims.append(Claim(
            claim_text=text,
            source_url=source.url,
            source_name=source.source_name,
            source_type=source.metadata.get("source_type", "unknown"),
            retrieved_at=source.timestamp,
        ))

    return claims


def extract_all_claims(question: str, sources: list, log_fn=print) -> list:
    """Runs extraction across all sources, returns the combined claim list."""
    all_claims = []
    for source in sources:
        if source.validation_status != "valid":
            continue
        log_fn(f"Extracting claims from {source.source_name}...")
        claims = extract_claims(question, source)
        log_fn(f"  -> {len(claims)} claim(s) extracted")
        all_claims.extend(claims)
    return all_claims


if __name__ == "__main__":
    from fanout_fetcher import fetch_all_4_sources

    question = "How does quantum computing affect cryptography?"
    sources = fetch_all_4_sources(question)
    claims = extract_all_claims(question, sources)

    print(f"\n=== {len(claims)} total claims extracted ===")
    for c in claims:
        print(f"\n[{c.source_name}] {c.claim_text}")
        print(f"  URL: {c.source_url}")

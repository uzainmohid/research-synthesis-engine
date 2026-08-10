"""
Deep Research & Auto-Report Generator — Main Entry Point
============================================================
Runs the full Week 3 pipeline end-to-end:
  1. Fan out to 4 sources (Wikipedia, web search, arXiv, Semantic Scholar)
  2. Extract cited claims from each valid source
  3. Score each claim's source quality
  4. Assemble a structured report (summary, findings, conflicts, references)
  5. Export to DOCX
  6. Track the question in the persistent research queue

Usage:
    python run_deep_research.py research "Your question here"
    python run_deep_research.py list
"""

import sys
import json
from claim_schema import ResearchQueue, Claim
from fanout_fetcher import fetch_all_4_sources
from claim_extractor import extract_all_claims
from quality_scorer import score_all_claims
from report_assembler import assemble_report
from docx_export import export_to_docx


def safe_filename(text: str, max_len: int = 50) -> str:
    safe = "".join(c if c.isalnum() or c == " " else "" for c in text)
    return "_".join(safe.split())[:max_len]


VAGUE_QUESTION_STARTS = ("tell me about", "what is", "info on", "information about")


def validate_question(question: str) -> tuple:
    """Rejects questions that are too short/vague to research meaningfully.
    Deliberately simple and deterministic (no extra LLM call) — this is a
    fast, predictable guardrail, not a nuanced judgment call. Returns
    (is_valid, reason)."""

    question = question.strip()

    if not question:
        return False, "Question is empty."

    if len(question) < 15:
        return False, "Question is too short to research meaningfully (under 15 characters). Try adding more context — e.g. what aspect, timeframe, or angle you want covered."

    word_count = len(question.split())
    if word_count < 4:
        return False, f"Question has only {word_count} word(s) — too vague to fan out to sources effectively. Try a fuller question, e.g. 'What causes X?' or 'How does X affect Y?'."

    lowered = question.lower().strip().rstrip("?.")
    VAGUE_PRONOUNS = {"it", "this", "that", "them", "these", "those", "him", "her"}

    for starter in VAGUE_QUESTION_STARTS:
        if lowered.startswith(starter):
            remainder = lowered[len(starter):].strip()
            remainder_words = remainder.split()
            # Reject if nothing follows the generic starter, or if all that
            # follows is a vague pronoun with no actual topic named.
            if not remainder_words or all(w in VAGUE_PRONOUNS for w in remainder_words):
                return False, "Question is too generic — it doesn't name a specific topic. Try naming what 'it' refers to, e.g. 'Tell me about the causes of inflation' rather than 'Tell me about it'."

    return True, ""


def run_research(question: str):
    queue = ResearchQueue()
    entry_id = queue.add_question(question)
    queue.mark_in_progress(entry_id)

    print(f"=== Starting deep research: {question} ===")

    try:
        # Step 2: fan out to 4 sources
        sources = fetch_all_4_sources(question)

        # Step 3: extract claims
        claims = extract_all_claims(question, sources)

        # Step 4: score quality
        claims = score_all_claims(claims, sources)

        # Step 5: assemble report
        report = assemble_report(question, claims)

        # Save raw claims data (state file, per Step 1)
        base_name = safe_filename(question)
        claims_path = f"claims_{base_name}.json"
        with open(claims_path, "w", encoding="utf-8") as f:
            json.dump([c.to_dict() for c in claims], f, indent=2, ensure_ascii=False)

        # Step 6: export to DOCX
        docx_path = f"report_{base_name}.docx"
        export_to_docx(question, report, claims, docx_path)

        queue.mark_completed(entry_id, report_path=docx_path, claims_path=claims_path)

        print(f"\n✅ Done.")
        print(f"   Claims data: {claims_path}")
        print(f"   DOCX report: {docx_path}")
        print(f"   Total claims extracted: {len(claims)}")
        print(f"   Conflicts/gaps noted: {len(report.get('conflicts_and_gaps', []))}")

    except Exception as e:
        queue.mark_failed(entry_id, reason=str(e))
        print(f"\n❌ Research failed: {e}")
        raise


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print('  python run_deep_research.py research "Your question here"')
        print("  python run_deep_research.py list")
        sys.exit(1)

    command = sys.argv[1]

    if command == "research":
        question = " ".join(sys.argv[2:])
        if not question:
            print('Usage: python run_deep_research.py research "Your question here"')
            sys.exit(1)

        is_valid, reason = validate_question(question)
        if not is_valid:
            print(f"❌ Question rejected: {reason}")
            print("   (Not added to the research queue — please rephrase and try again.)")
            sys.exit(1)

        run_research(question)

    elif command == "list":
        queue = ResearchQueue()
        queue.print_status()

    else:
        print(f"Unknown command: {command}")
        print("Valid commands: research, list")
        sys.exit(1)


if __name__ == "__main__":
    main()

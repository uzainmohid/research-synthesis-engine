"""
Multi-Source Fetcher
======================
For each sub-question, fetches from all 3 sources (Wikipedia, web search,
arXiv) and runs an extra relevance validation check on top of each
source's own validation. Logs every attempt (success or failure) to the
PipelineResult so nothing fails silently, and continues even if one or
more sources fail for a given sub-question.
"""

import re
from schema import SourceResult, SubQueryResult, PipelineResult
from test_wikipedia import fetch_wikipedia
from test_web_search import fetch_web_search
from test_arxiv import fetch_arxiv


def check_relevance(sub_query: str, content: str, min_overlap: int = 1) -> bool:
    """Very lightweight relevance check: does the content share at least
    `min_overlap` meaningful words with the sub-query? Uses 6-character
    PREFIX matching (not exact match) so word variants like
    'cryptography' vs 'cryptographic', or 'compute' vs 'computing',
    still count as the same topic — exact matching was rejecting
    genuinely relevant content just because of word endings."""
    if not content:
        return False

    def keywords(text):
        words = re.findall(r"[a-zA-Z]{4,}", text.lower())
        stopwords = {"what", "when", "where", "does", "which", "about", "their", "these", "those", "with"}
        # Use a 6-char prefix (or the whole word if shorter) so that
        # 'cryptography' and 'cryptographic' both map to 'crypto', and
        # 'computing' / 'computer' both map to 'comput'.
        return {w[:6] for w in words if w not in stopwords}

    query_words = keywords(sub_query)
    content_words = keywords(content)
    overlap = query_words & content_words
    return len(overlap) >= min_overlap


def fetch_all_sources(sub_query: str, pipeline: PipelineResult) -> SubQueryResult:
    """Fetches from all 3 sources for one sub-question, validates each,
    logs results, and returns a SubQueryResult (even if some/all sources
    failed — the pipeline continues regardless)."""

    result = SubQueryResult(sub_query=sub_query)
    fetchers = [
        ("wikipedia", fetch_wikipedia),
        ("web_search", fetch_web_search),
        ("arxiv", fetch_arxiv),
    ]

    for source_name, fetch_fn in fetchers:
        pipeline.log_event(f"Fetching '{sub_query}' from {source_name}...")

        try:
            source_result = fetch_fn(sub_query)
        except Exception as e:
            # Safety net: even an unexpected crash in a fetcher becomes a
            # logged failure, not a pipeline crash.
            source_result = SourceResult(
                source_name=source_name,
                query=sub_query,
                raw_content="",
                timestamp=SourceResult.now(),
                validation_status="failed",
                validation_reason=f"Unexpected error: {e}",
            )

        # Extra relevance check layered on top of the source's own validation
        if source_result.validation_status == "valid":
            if not check_relevance(sub_query, source_result.raw_content):
                source_result.validation_status = "invalid"
                source_result.validation_reason = "Content did not overlap meaningfully with the sub-query (relevance check failed)"

        if source_result.validation_status == "valid":
            pipeline.log_event(f"  -> {source_name}: VALID ({len(source_result.raw_content)} chars)")
        else:
            pipeline.log_event(f"  -> {source_name}: {source_result.validation_status.upper()} — {source_result.validation_reason}")

        result.source_results.append(source_result)

    valid_count = len(result.valid_results())
    pipeline.log_event(f"Sub-query '{sub_query}' complete: {valid_count}/3 sources valid.")

    return result


if __name__ == "__main__":
    import sys
    from query_parser import parse_query

    query = " ".join(sys.argv[1:]) or "How does quantum computing affect cryptography?"
    pipeline = PipelineResult(original_query=query)

    pipeline.log_event(f"Starting pipeline for: {query}")
    sub_queries = parse_query(query)
    pipeline.log_event(f"Parsed into {len(sub_queries)} sub-questions: {sub_queries}")

    for sq in sub_queries:
        sub_result = fetch_all_sources(sq, pipeline)
        pipeline.sub_query_results.append(sub_result)

    pipeline.log_event("Pipeline run complete.")
    pipeline.to_json("day2_test_output.json")
    print("\nSaved full result to day2_test_output.json")

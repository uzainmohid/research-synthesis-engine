"""
Fan-Out Fetcher (Step 2)
===========================
For a single research question, queries all 4 sources (Wikipedia,
web search, arXiv, Semantic Scholar) and validates each result.
Unlike Week 2's fetcher (which fanned out per SUB-question), this
fans out once per QUESTION, per the Week 3 spec ("For a question,
query at least 4 sources").
"""

import re
import threading
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI
from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL
from query_optimizer import optimize_query
from schema import SourceResult
from test_wikipedia import fetch_wikipedia
from test_web_search import fetch_web_search
from test_arxiv import fetch_arxiv
from semantic_scholar_source import fetch_semantic_scholar

SOURCE_TYPE_MAP = {
    "wikipedia": "encyclopedia",
    "web_search": "general_web",
    "arxiv": "academic_paper",
    "semantic_scholar": "academic_paper",
}

_log_lock = threading.Lock()  # keeps interleaved log lines from different threads readable


def _keyword_overlap_fallback(query: str, content: str, min_overlap: int = 2) -> bool:
    """Fallback ONLY used if the LLM relevance check is unavailable
    (no API key, or the API call itself fails). Not the primary check —
    kept purely so the pipeline still produces a reasonable result
    instead of crashing when DeepSeek is unreachable."""
    def keywords(text):
        words = re.findall(r"[a-zA-Z]{4,}", text.lower())
        stopwords = {"what", "when", "where", "does", "which", "about", "their", "these", "those", "with"}
        return {w[:6] for w in words if w not in stopwords}
    return len(keywords(query) & keywords(content)) >= min_overlap


def check_relevance(query: str, content: str) -> bool:
    """Judges whether `content` is genuinely relevant to `query` using
    the LLM (understands MEANING, not just shared words) — this is the
    general-purpose check meant to work on ANY topic, not just the ones
    tested during development. A keyword-overlap heuristic was tried
    first but kept producing false positives/negatives on words that
    are generic in one domain but meaningful in another (e.g. 'health'),
    which doesn't generalize. Falls back to a rough keyword check only
    if the LLM itself is unavailable."""
    if not content:
        return False

    if not DEEPSEEK_API_KEY:
        return _keyword_overlap_fallback(query, content)

    try:
        client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
        response = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": (
                    "You judge whether a piece of text is genuinely relevant to a "
                    "research question — i.e. whether it actually helps answer it, "
                    "not just whether it shares some vocabulary. Answer with the "
                    "single word YES or NO as the first word of your reply."
                )},
                {"role": "user", "content": f"Question: {query}\n\nText:\n{content[:1500]}"},
            ],
            temperature=0,
            max_tokens=20,  # small but not so tight it truncates the answer to nothing
        )
        raw = response.choices[0].message.content or ""
        answer = raw.strip().upper()

        if not answer:
            # Empty response from the model (still possible occasionally) —
            # don't silently treat that as "irrelevant", fall back instead.
            return _keyword_overlap_fallback(query, content)

        return "YES" in answer[:10]  # check near the start, tolerant of minor formatting

    except Exception:
        # LLM call failed (network issue, rate limit, etc.) — fall back
        # rather than blocking the whole pipeline on this one check.
        return _keyword_overlap_fallback(query, content)


def _fetch_one(source_name: str, fetch_fn, search_query: str, original_question: str, log_fn) -> SourceResult:
    """Runs one source's fetch (using the OPTIMIZED search_query, so
    Wikipedia/arXiv/Semantic Scholar get a short keyword phrase instead
    of a full sentence) on a worker thread. Relevance is then judged
    against the ORIGINAL question, since that's what actually needs
    answering — the optimized phrase is only a search aid, not a
    replacement for the user's real intent."""
    with _log_lock:
        log_fn(f"Fetching from {source_name}...")

    try:
        result = fetch_fn(search_query)
    except Exception as e:
        result = SourceResult(
            source_name=source_name, query=original_question, raw_content="",
            timestamp=SourceResult.now(), validation_status="failed",
            validation_reason=f"Unexpected error: {e}",
        )

    result.query = original_question  # keep the ORIGINAL question attached to the result

    if result.validation_status == "valid" and not check_relevance(original_question, result.raw_content):
        result.validation_status = "invalid"
        result.validation_reason = "Content did not overlap meaningfully with the question (relevance check failed)"

    result.metadata["source_type"] = SOURCE_TYPE_MAP.get(source_name, "unknown")
    result.metadata["search_query_used"] = search_query

    with _log_lock:
        if result.validation_status == "valid":
            log_fn(f"  -> {source_name}: VALID ({len(result.raw_content)} chars)")
        else:
            log_fn(f"  -> {source_name}: {result.validation_status.upper()} — {result.validation_reason}")

    return result


def fetch_all_4_sources(question: str, log_fn=print) -> list:
    """Fetches from all 4 sources for one research question IN PARALLEL
    (each source runs on its own thread, since these are independent
    network I/O calls — no reason to wait for one before starting the
    next). The question is first converted into a short, search-friendly
    keyword phrase (once, shared across all 4 sources) since full
    sentences make weak search queries for Wikipedia/arXiv/Semantic
    Scholar. Returns a list of SourceResult in a fixed, deterministic
    order (wikipedia, web_search, arxiv, semantic_scholar) regardless
    of which thread finishes first. Never raises — a source failure
    becomes a logged SourceResult with validation_status='failed'."""

    search_query = optimize_query(question)
    if search_query != question:
        log_fn(f"Optimized search query: '{search_query}' (from: '{question}')")

    fetchers = [
        ("wikipedia", fetch_wikipedia),
        ("web_search", fetch_web_search),
        ("arxiv", fetch_arxiv),
        ("semantic_scholar", fetch_semantic_scholar),
    ]

    results_by_source = {}
    with ThreadPoolExecutor(max_workers=4) as executor:
        future_to_name = {
            executor.submit(_fetch_one, name, fn, search_query, question, log_fn): name
            for name, fn in fetchers
        }
        for future in as_completed(future_to_name):
            name = future_to_name[future]
            results_by_source[name] = future.result()

    # Return in a fixed order, not thread-completion order, so downstream
    # code (and your report/log output) stays consistent across runs.
    results = [results_by_source[name] for name, _ in fetchers]

    valid_count = sum(1 for r in results if r.validation_status == "valid")
    log_fn(f"Fan-out complete: {valid_count}/4 sources valid.")

    return results


if __name__ == "__main__":
    import sys
    question = " ".join(sys.argv[1:]) or "How does quantum computing affect cryptography?"
    results = fetch_all_4_sources(question)
    for r in results:
        print(f"\n{r.source_name}: {r.validation_status}")

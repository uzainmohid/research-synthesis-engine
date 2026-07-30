"""
Test Source 3: arXiv (Academic Papers)
=========================================
Uses arXiv's free public API (no key needed) to search academic papers.
Run this file directly to test the source in isolation before it's
wired into the full pipeline.
"""

import time
import requests
import xml.etree.ElementTree as ET
from schema import SourceResult

ARXIV_API ="http://export.arxiv.org/api/query"
ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}

# arXiv's API asks for at least 3 seconds between requests — we track the
# last call time globally so the pipeline never violates this, no matter
# how many sub-questions are being processed in one run.
_last_call_time = 0.0
_MIN_INTERVAL_SECONDS = 3.0


def _wait_for_rate_limit():
    global _last_call_time
    elapsed = time.time() - _last_call_time
    if elapsed < _MIN_INTERVAL_SECONDS:
        time.sleep(_MIN_INTERVAL_SECONDS - elapsed)
    _last_call_time = time.time()


def fetch_arxiv(query: str, max_results: int = 3, _retries: int = 2) -> SourceResult:
    timestamp = SourceResult.now()
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results,
        "sortBy": "relevance",
        "sortOrder": "descending",
    }

    response = None
    last_error = None

    for attempt in range(_retries + 1):
        _wait_for_rate_limit()
        try:
            response = requests.get(ARXIV_API, params=params, timeout=30)
        except requests.RequestException as e:
            last_error = f"Request error: {e}"
            response = None
            continue  # retry

        if response.status_code == 429:
            last_error = "HTTP 429 (rate limited)"
            time.sleep(5)  # extra backoff before retrying a 429 specifically
            response = None
            continue

        break  # got a response (200 or other non-429 status) — stop retrying

    if response is None:
        return SourceResult(
            source_name="arxiv",
            query=query,
            raw_content="",
            timestamp=timestamp,
            validation_status="failed",
            validation_reason=last_error or "Unknown error after retries",
        )

    if response.status_code != 200:
        return SourceResult(
            source_name="arxiv",
            query=query,
            raw_content="",
            timestamp=timestamp,
            validation_status="failed",
            validation_reason=f"HTTP {response.status_code}",
        )

    try:
        root = ET.fromstring(response.text)
        entries = root.findall("atom:entry", ATOM_NS)
    except ET.ParseError as e:
        return SourceResult(
            source_name="arxiv",
            query=query,
            raw_content="",
            timestamp=timestamp,
            validation_status="failed",
            validation_reason=f"XML parse error: {e}",
        )

    if not entries:
        return SourceResult(
            source_name="arxiv",
            query=query,
            raw_content="",
            timestamp=timestamp,
            validation_status="invalid",
            validation_reason="No papers found for this query",
        )

    papers = []
    for entry in entries:
        title = entry.findtext("atom:title", default="", namespaces=ATOM_NS).strip()
        summary = entry.findtext("atom:summary", default="", namespaces=ATOM_NS).strip()
        published = entry.findtext("atom:published", default="", namespaces=ATOM_NS)
        link = entry.findtext("atom:id", default="", namespaces=ATOM_NS)
        papers.append(f"Title: {title}\nPublished: {published}\nSummary: {summary}\nLink: {link}")

    combined = "\n\n---\n\n".join(papers)

    return SourceResult(
        source_name="arxiv",
        query=query,
        raw_content=combined,
        timestamp=timestamp,
        validation_status="valid",
        url=entries[0].findtext("atom:id", default="", namespaces=ATOM_NS),
        metadata={"paper_count": len(papers)},
    )


if __name__ == "__main__":
    import sys
    query = " ".join(sys.argv[1:]) or "quantum computing cryptography"
    result = fetch_arxiv(query)
    print(f"\n--- arXiv test: '{query}' ---")
    print(f"Status: {result.validation_status}")
    if result.validation_reason:
        print(f"Reason: {result.validation_reason}")
    print(f"Content preview: {result.raw_content[:500]}")

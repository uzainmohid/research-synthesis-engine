"""
Source 4: Semantic Scholar
=============================
Free, no-API-key academic search API. Chosen as the 4th source because
it returns structured metadata (citation count, publication year,
venue, authors) that's directly useful for quality scoring — arXiv's
API doesn't reliably give citation counts, but Semantic Scholar does.
"""

import os
import time
import requests
from schema import SourceResult

SEMANTIC_SCHOLAR_API = "https://api.semanticscholar.org/graph/v1/paper/search"
SEMANTIC_SCHOLAR_API_KEY = os.environ.get("SEMANTIC_SCHOLAR_API_KEY", "")

_last_call_time = 0.0
# Unauthenticated requests share a rate-limited pool across ALL users of the
# public internet, so we space requests out generously and retry patiently.
# With a free dedicated API key (optional — request one at
# https://www.semanticscholar.org/product/api), the limit is much higher,
# so we can space requests closer together.
_MIN_INTERVAL_SECONDS = 0.5 if SEMANTIC_SCHOLAR_API_KEY else 3.0


def _wait_for_rate_limit():
    global _last_call_time
    elapsed = time.time() - _last_call_time
    if elapsed < _MIN_INTERVAL_SECONDS:
        time.sleep(_MIN_INTERVAL_SECONDS - elapsed)
    _last_call_time = time.time()


def fetch_semantic_scholar(query: str, max_results: int = 3, _retries: int = 4) -> SourceResult:
    timestamp = SourceResult.now()
    params = {
        "query": query,
        "limit": max_results,
        "fields": "title,abstract,year,citationCount,authors,venue,url,externalIds",
    }
    headers = {"x-api-key": SEMANTIC_SCHOLAR_API_KEY} if SEMANTIC_SCHOLAR_API_KEY else {}

    response = None
    last_error = None

    for attempt in range(_retries + 1):
        _wait_for_rate_limit()
        try:
            response = requests.get(SEMANTIC_SCHOLAR_API, params=params, headers=headers, timeout=20)
        except requests.RequestException as e:
            last_error = f"Request error: {e}"
            response = None
            continue

        if response.status_code == 429:
            last_error = "HTTP 429 (rate limited)"
            time.sleep(8)
            response = None
            continue

        break

    if response is None:
        return SourceResult(source_name="semantic_scholar", query=query, raw_content="", timestamp=timestamp,
                             validation_status="failed", validation_reason=last_error or "Unknown error after retries")

    if response.status_code != 200:
        return SourceResult(source_name="semantic_scholar", query=query, raw_content="", timestamp=timestamp,
                             validation_status="failed", validation_reason=f"HTTP {response.status_code}")

    data = response.json()
    papers = data.get("data", [])

    if not papers:
        return SourceResult(source_name="semantic_scholar", query=query, raw_content="", timestamp=timestamp,
                             validation_status="invalid", validation_reason="No papers found for this query")

    blocks = []
    top_paper = papers[0]
    for p in papers:
        if not p.get("abstract"):
            continue
        authors = ", ".join(a.get("name", "") for a in p.get("authors", [])[:5])
        blocks.append(
            f"Title: {p.get('title', '')}\n"
            f"Year: {p.get('year', 'unknown')}\n"
            f"Citations: {p.get('citationCount', 0)}\n"
            f"Venue: {p.get('venue', 'unknown')}\n"
            f"Authors: {authors}\n"
            f"Abstract: {p.get('abstract', '')}\n"
            f"URL: {p.get('url', '')}"
        )

    if not blocks:
        return SourceResult(source_name="semantic_scholar", query=query, raw_content="", timestamp=timestamp,
                             validation_status="invalid", validation_reason="Papers found but none had abstracts")

    combined = "\n\n---\n\n".join(blocks)

    return SourceResult(
        source_name="semantic_scholar",
        query=query,
        raw_content=combined,
        timestamp=timestamp,
        validation_status="valid",
        url=top_paper.get("url", ""),
        metadata={
            "paper_count": len(blocks),
            "top_citation_count": top_paper.get("citationCount", 0),
            "top_year": top_paper.get("year"),
        },
    )


if __name__ == "__main__":
    import sys
    query = " ".join(sys.argv[1:]) or "quantum computing cryptography"
    result = fetch_semantic_scholar(query)
    print(f"\n--- Semantic Scholar test: '{query}' ---")
    print(f"Status: {result.validation_status}")
    if result.validation_reason:
        print(f"Reason: {result.validation_reason}")
    print(f"Content preview: {result.raw_content[:500]}")

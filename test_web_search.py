"""
Test Source 2: General Web Search
====================================
Uses the free 'ddgs' package (DuckDuckGo search, no API key required)
to run a general web query. Run this file directly to test the source
in isolation before it's wired into the full pipeline.
"""

from ddgs import DDGS
from schema import SourceResult


def fetch_web_search(query: str, max_results: int = 5) -> SourceResult:
    timestamp = SourceResult.now()

    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
    except Exception as e:
        return SourceResult(
            source_name="web_search",
            query=query,
            raw_content="",
            timestamp=timestamp,
            validation_status="failed",
            validation_reason=f"Search error: {e}",
        )

    if not results:
        return SourceResult(
            source_name="web_search",
            query=query,
            raw_content="",
            timestamp=timestamp,
            validation_status="invalid",
            validation_reason="No results returned",
        )

    # Combine top results into one text block, keep source URLs in metadata
    combined = "\n\n".join(
        f"{r.get('title', '')}: {r.get('body', '')}" for r in results
    )
    urls = [r.get("href", "") for r in results]

    return SourceResult(
        source_name="web_search",
        query=query,
        raw_content=combined,
        timestamp=timestamp,
        validation_status="valid",
        url=urls[0] if urls else "",
        metadata={"result_count": len(results), "urls": urls},
    )


if __name__ == "__main__":
    import sys
    query = " ".join(sys.argv[1:]) or "quantum computing impact on cryptography"
    result = fetch_web_search(query)
    print(f"\n--- Web search test: '{query}' ---")
    print(f"Status: {result.validation_status}")
    if result.validation_reason:
        print(f"Reason: {result.validation_reason}")
    print(f"Content preview: {result.raw_content[:400]}")

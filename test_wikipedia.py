"""
Test Source 1: Wikipedia
=========================
Uses Wikipedia's free public REST API (no key needed) to fetch a
page summary. Run this file directly to test the source in isolation
before it's wired into the full pipeline.
"""

import requests
from schema import SourceResult

WIKI_SEARCH_API = "https://en.wikipedia.org/w/api.php"
WIKI_SUMMARY_API = "https://en.wikipedia.org/api/rest_v1/page/summary/{title}"


def find_best_title(topic: str) -> str:
    """Searches Wikipedia and returns the best-matching article title.
    This is necessary because sub-questions (e.g. 'What is Shor's algorithm?')
    are not themselves valid page titles ('Shor's algorithm' is)."""
    params = {
        "action": "query",
        "list": "search",
        "srsearch": topic,
        "format": "json",
        "srlimit": 1,
    }
    try:
        response = requests.get(
            WIKI_SEARCH_API, params=params, timeout=10,
            headers={"User-Agent": "ResearchSynthesisEngine/1.0"},
        )
        response.raise_for_status()
        results = response.json().get("query", {}).get("search", [])
        if results:
            return results[0]["title"]
    except requests.RequestException:
        pass
    return topic  # fallback: try the raw topic as a title if search fails


def fetch_wikipedia(topic: str) -> SourceResult:
    timestamp = SourceResult.now()

    best_title = find_best_title(topic)
    url = WIKI_SUMMARY_API.format(title=best_title.replace(" ", "_"))

    try:
        response = requests.get(url, timeout=10, headers={"User-Agent": "ResearchSynthesisEngine/1.0"})
    except requests.RequestException as e:
        return SourceResult(
            source_name="wikipedia",
            query=topic,
            raw_content="",
            timestamp=timestamp,
            validation_status="failed",
            validation_reason=f"Request error: {e}",
            url=url,
        )

    if response.status_code != 200:
        return SourceResult(
            source_name="wikipedia",
            query=topic,
            raw_content="",
            timestamp=timestamp,
            validation_status="failed",
            validation_reason=f"HTTP {response.status_code}",
            url=url,
        )

    data = response.json()
    extract = data.get("extract", "")

    # Validation: must have real content, and it shouldn't be a disambiguation stub
    if not extract or len(extract) < 40:
        return SourceResult(
            source_name="wikipedia",
            query=topic,
            raw_content=extract,
            timestamp=timestamp,
            validation_status="invalid",
            validation_reason="Content too short or empty — likely no article found",
            url=data.get("content_urls", {}).get("desktop", {}).get("page", url),
        )

    return SourceResult(
        source_name="wikipedia",
        query=topic,
        raw_content=extract,
        timestamp=timestamp,
        validation_status="valid",
        url=data.get("content_urls", {}).get("desktop", {}).get("page", url),
        metadata={"title": data.get("title", topic)},
    )


if __name__ == "__main__":
    import sys
    topic = " ".join(sys.argv[1:]) or "Quantum computing"
    result = fetch_wikipedia(topic)
    print(f"\n--- Wikipedia test: '{topic}' ---")
    print(f"Status: {result.validation_status}")
    if result.validation_reason:
        print(f"Reason: {result.validation_reason}")
    print(f"URL: {result.url}")
    print(f"Content preview: {result.raw_content[:300]}")

"""
Quality Scorer (Step 4)
===========================
Scores each Claim's source on a 0.0-1.0 scale based on:
  + recency:   published/current within the last 2 years
  + authority: .edu/.gov domain, OR a high citation count (academic sources)
  - unknown authorship: no identifiable author/institution (penalized)

This score is attached to the Claim itself so the report can weight
and order findings by source reliability.
"""

from datetime import datetime, timezone
from urllib.parse import urlparse
from claim_schema import Claim
from schema import SourceResult

CURRENT_YEAR = datetime.now(timezone.utc).year
RECENCY_WINDOW_YEARS = 2
HIGH_CITATION_THRESHOLD = 10

AUTHORITATIVE_TLDS = (".edu", ".gov")

# Sources whose authorship is institutional/attributable even without a
# named individual author (Wikipedia = collaborative encyclopedia,
# arXiv/Semantic Scholar = named academic authors in metadata).
KNOWN_AUTHORSHIP_SOURCES = {"wikipedia", "arxiv", "semantic_scholar"}


def score_claim(claim: Claim, source_metadata: dict) -> float:
    """Returns a quality score in [0.0, 1.0]. source_metadata is the
    .metadata dict from the SourceResult this claim came from (carries
    things like top_year, top_citation_count for academic sources)."""

    score = 0.5  # neutral baseline

    # --- Recency ---
    year = source_metadata.get("top_year")
    if claim.source_name in ("arxiv", "semantic_scholar") and year:
        if CURRENT_YEAR - int(year) <= RECENCY_WINDOW_YEARS:
            score += 0.25
        else:
            score -= 0.10
    # Wikipedia and web_search are continuously updated, so we treat
    # them as recency-neutral rather than penalizing or rewarding them.

    # --- Authority: domain check ---
    domain = urlparse(claim.source_url).netloc.lower()
    is_authoritative_domain = any(domain.endswith(tld) for tld in AUTHORITATIVE_TLDS)

    # --- Authority: citation count (academic sources only) ---
    citation_count = source_metadata.get("top_citation_count", 0) or 0
    is_highly_cited = claim.source_name == "semantic_scholar" and citation_count >= HIGH_CITATION_THRESHOLD

    if is_authoritative_domain or is_highly_cited:
        score += 0.25

    # Wikipedia gets a smaller, separate authority nod: widely
    # cross-checked and continuously edited, but not .edu/.gov and not
    # peer-reviewed, so it earns less than a true authoritative source.
    if claim.source_name == "wikipedia":
        score += 0.10

    # --- Unknown authorship penalty ---
    if claim.source_name not in KNOWN_AUTHORSHIP_SOURCES:
        score -= 0.15  # e.g. general web_search results with no clear author

    return round(max(0.0, min(1.0, score)), 2)


def score_all_claims(claims: list, sources: list) -> list:
    """Scores every claim in place (mutates and returns the same list).
    Looks up each claim's source metadata by matching source_name."""

    metadata_by_source = {s.source_name: s.metadata for s in sources}

    for claim in claims:
        source_meta = metadata_by_source.get(claim.source_name, {})
        claim.quality_score = score_claim(claim, source_meta)

    return claims


if __name__ == "__main__":
    # Quick smoke test with fake data
    test_claim_academic = Claim(
        claim_text="Test claim from a recent, highly-cited paper",
        source_url="https://arxiv.org/abs/1234",
        source_name="semantic_scholar",
        source_type="academic_paper",
        retrieved_at=SourceResult.now(),
    )
    score = score_claim(test_claim_academic, {"top_year": CURRENT_YEAR, "top_citation_count": 50})
    print(f"Recent, highly-cited academic claim score: {score}")

    test_claim_web = Claim(
        claim_text="Test claim from a random blog",
        source_url="https://someblog.example.com/post",
        source_name="web_search",
        source_type="general_web",
        retrieved_at=SourceResult.now(),
    )
    score = score_claim(test_claim_web, {})
    print(f"Random web blog claim score: {score}")

    test_claim_gov = Claim(
        claim_text="Test claim from a .gov source",
        source_url="https://nasa.gov/some-page",
        source_name="web_search",
        source_type="general_web",
        retrieved_at=SourceResult.now(),
    )
    score = score_claim(test_claim_gov, {})
    print(f".gov-domain web claim score: {score}")

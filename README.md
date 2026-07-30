# Multi-Source Research Synthesis Engine

A research automation pipeline that takes a complex question, decomposes it into sub-questions, gathers information from three independent sources (Wikipedia, general web search, and arXiv academic papers), cross-references the results, resolves contradictions between sources, and produces a structured markdown research report — complete with confidence ratings and full source provenance.

Built during Week 2 of my Hoardy AI internship.

---

## What it does

Give it a question like *"How does quantum computing affect cryptography?"* and it will:

1. **Parse** the question into 2–4 focused sub-questions using an LLM (DeepSeek Flash)
2. **Fetch** each sub-question from three independent sources in parallel:
   - **Wikipedia** — via a search-then-summarize step against Wikipedia's public REST API
   - **General web search** — via DuckDuckGo (`ddgs`), no API key required
   - **arXiv** — academic papers via arXiv's public API, rate-limited and retried correctly
3. **Validate** every single result — checking for empty/short content and topical relevance — before it's allowed into the next stage
4. **Synthesize** the valid results per sub-question, explicitly detecting and explaining any contradictions between sources (e.g. differing statistics, outdated vs. current figures)
5. **Generate** a structured markdown report: Executive Summary, Key Findings (with confidence ratings), a Source Provenance table, an Overall Confidence Rating, and a full timestamped Pipeline Log

If any source fails — a timeout, a bad response, an irrelevant result — the pipeline logs it and **keeps going**, producing a partial-but-complete report from whatever sources succeeded, rather than crashing.

---

## Architecture

```
User Query
    │
    ▼
┌─────────────────────┐
│   Query Parser       │  (query_parser.py)
│   DeepSeek Flash LLM  │  → splits into 2-4 sub-questions
└──────────┬───────────┘
           │
           ▼
┌─────────────────────────────────────────────┐
│           Multi-Source Fetcher                │  (fetcher.py)
│                                                 │
│   For each sub-question, fetch in parallel:    │
│   ┌───────────┐ ┌────────────┐ ┌───────────┐  │
│   │ Wikipedia │ │ Web Search │ │   arXiv   │  │
│   │  (REST)   │ │  (ddgs)    │ │ (Atom API)│  │
│   └─────┬─────┘ └──────┬─────┘ └─────┬─────┘  │
│         └──────────────┼──────────────┘        │
│                         ▼                        │
│              Per-source validation                │
│         (content present? topically relevant?)    │
└──────────────────────┬──────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────┐
│      Synthesis & Cross-Reference   │  (synthesis.py)
│      DeepSeek Flash LLM            │
│  → combines valid sources per      │
│    sub-question, flags conflicts,  │
│    assigns a confidence rating     │
└──────────────┬────────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│      Markdown Report Generator     │  (report_generator.py)
│  → Executive Summary               │
│  → Key Findings + confidence       │
│  → Source Provenance table         │
│  → Overall Confidence Rating       │
│  → Full Pipeline Log               │
└─────────────────────────────────┘
```

`run_pipeline.py` orchestrates all four stages end-to-end for a single command-line query.

---

## Tech stack

| Component | Tool |
|---|---|
| Agent / LLM orchestration | DeepSeek Flash (`deepseek-v4-flash`) via OpenAI-compatible API |
| Wikipedia access | Wikipedia public REST API (search + summary) |
| Web search | `ddgs` (DuckDuckGo search, free, no API key) |
| Academic source | arXiv public API (Atom/XML) |
| Report format | Markdown |
| Language | Python 3.11+ |

---

## Project structure

```
research-synthesis-engine/
├── schema.py            # Data structures: SourceResult, SubQueryResult, PipelineResult
├── config.py             # Loads DEEPSEEK_API_KEY from .env
├── query_parser.py       # Splits a query into sub-questions (DeepSeek)
├── test_wikipedia.py     # Wikipedia source: search + fetch summary
├── test_web_search.py    # Web search source: ddgs
├── test_arxiv.py         # arXiv source: rate-limited, retried
├── fetcher.py             # Orchestrates all 3 sources per sub-question + relevance validation
├── synthesis.py           # Cross-references sources, flags conflicts, rates confidence
├── report_generator.py    # Builds the final markdown report
├── run_pipeline.py         # Main entry point — runs the full pipeline end-to-end
├── requirements.txt
├── .env.example
└── reports/                # Generated markdown reports (sample queries)
```

---

## How to run it

```bash
python -m venv venv
.\venv\Scripts\Activate.ps1        # Windows PowerShell
pip install -r requirements.txt
```

Create a `.env` file (see `.env.example`) with your DeepSeek API key:
```
DEEPSEEK_API_KEY=your_key_here
```

Then run any query:
```bash
python run_pipeline.py "How does quantum computing affect cryptography?"
```

This produces `pipeline_output.json` (raw structured data) and a `report_<query>.md` file (the final report).

---

## Testing & validation

### Individual source testing
Each source can be tested in isolation before being wired into the pipeline:
```bash
python test_wikipedia.py "Quantum computing"
python test_web_search.py "quantum computing impact on cryptography"
python test_arxiv.py "quantum computing cryptography"
```
See `query_parsing_terminaltest.png` — all three sources tested individually and returning valid, relevant content.

### Conflict detection testing
To specifically prove the cross-referencing and contradiction-resolution logic, I ran queries on topics known to have numbers that change over time or vary by source (moon counts, exoplanet counts) — a reliable way to surface genuine disagreement between sources rather than relying on chance.

Example: *"How many moons does Saturn have?"* surfaced a real conflict — one source reported 274 moons, another reported 285 — which the synthesis layer correctly flagged and resolved by recency. See `conflictstesting.png` for the terminal output showing `Conflicts found: 1` and `Conflicts found: 2` across sub-questions in this run.

Across 8 test queries total, conflicts were correctly detected and explained on 4 separate real-world cases (Saturn's moons, Jupiter's moons, exoplanet counts, and a vaccine-related web snippet that contained an internally inconsistent statement).

### Edge case testing — source failure handling
To verify the pipeline degrades gracefully when a source is unavailable, I intentionally broke the arXiv endpoint (pointing it at a non-existent hostname) and reran a query. See `edgecastetest1.png` for the terminal output:

- arXiv failed with a connection error (`NameResolutionError`, unresolvable host) on every sub-question
- The pipeline logged each failure clearly (`arxiv: FAILED — Request error: ...`) and **did not crash**
- It continued fetching from Wikipedia and web search, completed synthesis with 2/3 sources, and finished the full run (`=== Pipeline run complete ===`)

I also encountered a **real, unforced arXiv timeout** during normal testing (not staged) — the pipeline handled it identically: logged the failure, produced a partial result, and completed successfully. This is stronger evidence of resilience than a synthetic test alone, since it reflects an actual third-party outage under real conditions.

---

## Sample reports

The `reports/` folder contains 8 generated research reports covering a range of topics and outcomes:

| Report | Purpose |
|---|---|
| `quantum_computing_cryptography.md` | Core functionality, multi-source agreement |
| `saturn_moons.md` | Conflict detection (2 conflicts found), plus a real arXiv timeout handled gracefully |
| `jupiter_moons.md` | Conflict detection (1 conflict found) |
| `exoplanets_discovered.md` | Conflict detection (1 conflict found) |
| `electric_vehicles_environment.md` | Multi-source synthesis, no conflicts (topic has general consensus) |
| `photosynthesis.md` | Clean synthesis across all 3 sources, high confidence |
| `theory_of_relativity.md` | Source validation correctly rejecting an irrelevant arXiv result |
| `vaccines_immunity.md` | Conflict detection (2 conflicts found), including catching an internally inconsistent web snippet |

---

## Design decisions & challenges

- **Wikipedia search-before-fetch:** initially the pipeline tried to fetch a Wikipedia page using the full sub-question as the literal page title, which always 404'd. Fixed by adding a Wikipedia search step to resolve the actual article title first.
- **arXiv rate limiting:** arXiv's API requires a minimum 3-second gap between requests; without this, rapid sequential sub-question fetches triggered `HTTP 429` errors. Fixed with a global rate limiter plus retry-with-backoff.
- **Relevance false negatives:** the initial relevance check used exact word matching, which rejected genuinely relevant content over simple word-form differences (e.g. "cryptography" vs. "cryptographic"). Fixed by matching on word prefixes instead of exact strings.
- **Conflict-detection under-reporting:** the synthesis LLM initially treated resolvable discrepancies (e.g. a count that grew over time) as a narrative detail rather than a structured conflict to log. Fixed by explicitly instructing the model that numeric/statistical differences must always be logged in the structured conflicts list, even when a resolution is possible.
- **Graceful degradation by design:** every source fetch is wrapped so that a failure (network error, timeout, bad response) always produces a logged `SourceResult` with `validation_status="failed"` rather than raising an exception — this is what allows the pipeline to complete with partial data instead of crashing.

---

## Deliverables

- ✅ Working pipeline (`run_pipeline.py`), tested end-to-end on 8 distinct queries
- ✅ 5 generated markdown research reports (`reports/`)
- ✅ Source code for all pipeline stages
- ✅ Edge case testing proof (source-down simulation + a real unforced failure)
- ✅ Conflict detection proof (4 real conflicts across 4 different queries)
- ✅ This README
# Multi-Source Research Synthesis Engine   
# Deep Research & Auto-Report Generator week2/week3 project HOARDY AI

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

# WEEK 3 Project --- 


# Deep Research & Auto-Report Generator

An AI research agent that takes a question, gathers evidence from 4+ independent sources, extracts atomic claims with full per-claim citations, scores each source's quality, and produces a structured, professionally formatted DOCX research report — with every finding traceable to its source, and every disagreement between sources documented rather than hidden.

Built during Weeks 2–3 of my Hoardy AI internship. Started as a 3-source research synthesis engine (Week 2) and was extended into a citation-grade, 4-source deep research tool with claim-level attribution, quality scoring, and DOCX export (Week 3).

---

## What it does

Give it a question like *"What caused the collapse of the Roman Empire?"* and it will:

1. **Fan out to 4 sources in parallel** — Wikipedia, general web search, arXiv, and Semantic Scholar — each on its own thread
2. **Validate every result** — checking it actually has content, and that it's genuinely relevant to the question (judged by an LLM, not just keyword matching)
3. **Extract atomic claims** — each source's content is split into individual, citable factual statements, each bound to that exact source
4. **Score source quality** — recency, domain/citation authority, and known-authorship checks, so every claim carries a 0.0–1.0 reliability score
5. **Assemble a structured report** — Executive Summary, numbered Findings with inline `[1][2]` citations, a Conflicts & Gaps section (disagreements between sources are documented, never silently resolved by picking one), and a References list with full URLs
6. **Export to DOCX** — a clean, professional document, including an appendix table of every extracted claim and its quality score
7. **Track everything in a persistent research queue** — a JSON state file recording every question ever run, its status, and its output paths, so work isn't lost between sessions

If a source fails — a timeout, a rate limit, irrelevant content — the pipeline logs it and keeps going, producing a complete report from whatever sources succeeded.

---

## Architecture

```
User Question
    │
    ▼
┌─────────────────────────┐
│   Question Validator       │  (run_deep_research.py)
│   → rejects vague/empty     │
│     questions before they   │
│     enter the pipeline      │
└──────────┬──────────────┘
           ▼
┌─────────────────────────────────────────────────────┐
│              Parallel Fan-Out Fetcher                    │  (fanout_fetcher.py)
│                                                            │
│   ┌───────────┐ ┌──────────┐ ┌───────┐ ┌────────────┐    │
│   │ Wikipedia │ │Web Search│ │ arXiv │ │  Semantic  │    │
│   │  (REST)   │ │  (ddgs)  │ │(Atom) │ │  Scholar   │    │
│   └─────┬─────┘ └────┬─────┘ └───┬───┘ └─────┬──────┘    │
│         └────────────┼───────────┼───────────┘            │
│                       ▼                                     │
│         LLM-based relevance validation                      │
│    (judges MEANING, not just shared keywords)                │
└──────────────────────┬──────────────────────────────────┘
                        ▼
┌─────────────────────────────────┐
│      Claim Extractor               │  (claim_extractor.py)
│      DeepSeek Flash                 │
│  → splits each valid source into    │
│    2-4 atomic, citable claims        │
│  → conflicting claims from different │
│    sources are KEPT SEPARATE          │
└──────────────┬────────────────────┘
               ▼
┌─────────────────────────────────┐
│      Quality Scorer                │  (quality_scorer.py)
│  → recency + authority + author-    │
│    ship checks per claim's source    │
└──────────────┬────────────────────┘
               ▼
┌─────────────────────────────────┐
│      Report Assembler              │  (report_assembler.py)
│      DeepSeek Flash                 │
│  → Executive Summary                │
│  → Findings with [1][2] citations    │
│  → Conflicts & Gaps                  │
│  → References (deterministic,        │
│    built by code, not the LLM)        │
└──────────────┬────────────────────┘
               ▼
┌─────────────────────────────────┐
│      DOCX Exporter                 │  (docx_export.py)
│  → clean formatted report +          │
│    claims appendix table              │
└─────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│      Research Queue                 │  (claim_schema.py)
│  → persistent JSON state file        │
│    tracking every question run        │
└─────────────────────────────────┘
```

`run_deep_research.py` orchestrates all of this behind two commands:
```bash
python run_deep_research.py research "Your question here"
python run_deep_research.py list
```

---

## Scoring rules

Every claim's `quality_score` (0.0–1.0) starts at a neutral 0.5 baseline, then:

| Signal | Adjustment |
|---|---|
| Academic source (arXiv/Semantic Scholar) published within the last 2 years | **+0.25** |
| Academic source older than 2 years | **−0.10** |
| Source domain ends in `.edu` or `.gov` | **+0.25** |
| Semantic Scholar paper with 10+ citations | **+0.25** (same bucket as domain authority, not additive with it) |
| Wikipedia (collaborative, cross-checked, but not peer-reviewed) | **+0.10** |
| No identifiable author/institution (e.g. a general web search result with no byline) | **−0.15** |

Final score is clamped to `[0.0, 1.0]`.

---

## Key prompts

**Claim extraction** (`claim_extractor.py`) — instructs the model to extract 2-4 atomic factual claims per source, explicitly forbidding it from softening or reconciling claims across sources: *"Extract claims exactly as the source states them — do not soften, average, or reconcile them with what other sources might say."*

**Relevance judgment** (`fanout_fetcher.py`) — a lightweight LLM call per source: *"You judge whether a piece of text is genuinely relevant to a research question — i.e. whether it actually helps answer it, not just whether it shares some vocabulary."* This replaced an earlier keyword-overlap heuristic that produced false matches on generic shared words.

**Report assembly** (`report_assembler.py`) — instructs the model to document disagreements rather than resolve them silently: *"For each case where two or more claims genuinely disagree... describe both claims with their citation numbers and note the disagreement explicitly — do NOT pick one as correct and drop the other."* Citation numbers themselves are assigned deterministically by code, not the LLM, so they always match the References list exactly.

---

## How it handles failure gracefully

Every source fetch is wrapped so a failure never crashes the pipeline — it becomes a logged, structured result with `validation_status="failed"`, and the pipeline continues with whatever sources succeeded. This was proven under real conditions multiple times during testing, not just simulated:

```
Fetching from wikipedia...
Fetching from web_search...
Fetching from arxiv...
Fetching from semantic_scholar...
  -> arxiv: INVALID — Content did not overlap meaningfully with the question (relevance check failed)
  -> wikipedia: VALID (619 chars)
  -> web_search: VALID (1252 chars)
  -> semantic_scholar: FAILED — HTTP 429 (rate limited)
Fan-out complete: 2/4 sources valid.
...
✅ Done.
   Total claims extracted: 8
   Conflicts/gaps noted: 2
```

Two out of four sources failed here — one to a real external rate limit, one correctly rejected as off-topic — and the pipeline still produced a complete, cited, 8-claim report. See `graceful-failure-handling.png`.

---

## Challenges faced

- **Wikipedia 404s on Week 2:** the original fetcher treated a full sub-question as a literal Wikipedia page title. Fixed by adding a search-first step to resolve the real article title.
- **arXiv rate limiting:** arXiv's API requires a minimum gap between requests; rapid sequential calls triggered `HTTP 429`. Fixed with a global rate limiter and retry-with-backoff.
- **Relevance false positives:** an early keyword-overlap relevance check let an unrelated AI/healthcare-systems paper pass for a diet/fasting question, because both mentioned the generic word "health." Replaced the entire approach with an LLM-based relevance judgment that evaluates actual meaning instead of shared vocabulary — this generalizes to any topic rather than needing a growing, hand-tuned stopword list.
- **A real regression, caught and fixed:** an early version of the LLM relevance check capped the model's response at 5 tokens, which truncated its answer to nothing and caused every single source to be marked irrelevant. Fixed by giving the model room to respond and adding a safe fallback for empty responses — and this time verified with unit tests (mocked YES/NO/empty-response cases) before shipping, rather than shipping on reasoning alone.
- **Semantic Scholar's shared public rate limit:** the unauthenticated tier is shared globally and fails unpredictably. The pipeline treats this as expected, logs it clearly, and continues with the other 3 sources — this is real, organic proof of graceful degradation, not a bug to hide.
- **Query specificity:** added a lightweight, deterministic validator that rejects vague questions (e.g. "hi", "tell me about it") before they enter the pipeline, so the research queue only ever holds genuinely researchable questions.

---

## Project structure

```
research-synthesis-engine/
├── schema.py                  # Week 2: SourceResult, SubQueryResult, PipelineResult
├── config.py                  # Loads DEEPSEEK_API_KEY from .env
├── test_wikipedia.py          # Source: Wikipedia (search + summary)
├── test_web_search.py         # Source: general web (ddgs)
├── test_arxiv.py               # Source: arXiv (rate-limited, retried)
├── semantic_scholar_source.py  # Source: Semantic Scholar (citations, authors, year)
├── claim_schema.py             # Week 3: Claim dataclass + persistent ResearchQueue
├── fanout_fetcher.py            # Parallel 4-source fetch + LLM relevance validation
├── claim_extractor.py           # Splits sources into atomic, cited claims
├── quality_scorer.py            # Scores each claim's source quality
├── report_assembler.py          # Executive summary, findings, conflicts, references
├── docx_export.py                # Renders the final report to DOCX
├── run_deep_research.py          # Main entry point + query validation + queue CLI
├── requirements.txt
├── .env.example
└── reports/                      # Generated DOCX reports (9 sample questions)
```

---

## How to run it

```bash
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create `.env` with your DeepSeek key:
```
DEEPSEEK_API_KEY=your_key_here
```

Run a question:
```bash
python run_deep_research.py research "What caused the collapse of the Roman Empire?"
```

Check the research queue:
```bash
python run_deep_research.py list
```

---

## Deliverables

- ✅ Working deep-research agent — answers questions from 4+ sources with per-claim citations
- ✅ Exported DOCX report — `reports/report_What_caused_the_collapse_of_the_Roman_Empire.docx`
- ✅ Citation trail — every finding maps to a numbered reference with a full source URL; conflicts documented, not hidden
- ✅ Research queue — `research_queue.json`, showing 9 completed research tasks
- ✅ This README — architecture, scoring rules, prompts, and challenges faced
- ✅ Screenshots — see `/screenshots` for full pipeline runs, graceful failure handling, the exported report, and the research queue

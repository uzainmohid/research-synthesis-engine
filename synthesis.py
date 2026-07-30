"""
Synthesis & Cross-Reference Layer (Day 3)
============================================
For each sub-question, takes all VALID source results and asks DeepSeek
to synthesize them into one coherent finding, explicitly flagging any
contradictions between sources and how they were resolved (e.g. by
recency or source reliability).
"""

import json
from openai import OpenAI
from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL
from schema import SubQueryResult

SYNTHESIS_SYSTEM_PROMPT = """You are a research synthesis engine. You will be given
one sub-question and content from multiple sources (Wikipedia, general web search,
and/or arXiv academic papers). Your job:

1. Write a synthesized finding (2-4 sentences) that answers the sub-question,
   combining information across sources.
2. Identify any CONTRADICTIONS between sources — this includes DIRECT
   disagreements AND cases where sources report DIFFERENT NUMBERS, DATES,
   COUNTS, or STATISTICS for the same fact (e.g. one source says 95, another
   says 115) — even if you can explain the difference (such as one source
   being older/more recent). A resolvable discrepancy is STILL a conflict —
   log it in the conflicts list, don't just mention it in the synthesis
   paragraph and skip the list. For each conflict found, state what each
   source claims and how you resolved it (e.g. "Wikipedia says 95 moons
   (as of 2024), academic source says 115 moons (as of 2026). Resolution:
   the higher count reflects more recent discoveries."). Only return an
   empty list if sources genuinely report the exact same facts with no
   numeric or factual differences at all.
3. Rate your confidence as "high", "medium", or "low" based on: how many
   sources agree, and whether any source is notably more authoritative
   (academic papers > general web) or more recent.

Respond with ONLY a JSON object in this exact shape, nothing else:
{
  "synthesis": "...",
  "conflicts": ["Source A says X, Source B says Y. Resolution: ..."],
  "confidence": "high"
}
"""


def synthesize_subquery(sub_result: SubQueryResult) -> dict:
    """Returns {"synthesis": str, "conflicts": list[str], "confidence": str}.
    Degrades gracefully: if there's no valid data or the LLM call fails,
    still returns a usable (low-confidence) result instead of crashing."""

    valid_results = sub_result.valid_results()

    if not valid_results:
        return {
            "synthesis": f"No valid data could be gathered for this sub-question ('{sub_result.sub_query}'). All sources failed or returned irrelevant content.",
            "conflicts": [],
            "confidence": "none",
        }

    if not DEEPSEEK_API_KEY:
        # Fallback with no LLM available: just concatenate raw content
        combined = "\n\n".join(f"[{r.source_name}] {r.raw_content[:500]}" for r in valid_results)
        return {
            "synthesis": combined,
            "conflicts": [],
            "confidence": "low",
        }

    # Build the source content block for the prompt
    source_blocks = []
    for r in valid_results:
        source_blocks.append(f"--- Source: {r.source_name} (fetched {r.timestamp}) ---\n{r.raw_content[:1500]}")
    sources_text = "\n\n".join(source_blocks)

    user_prompt = f"Sub-question: {sub_result.sub_query}\n\n{sources_text}"

    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)

    try:
        response = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": SYNTHESIS_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )
        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            content = content.strip("`").replace("json", "", 1).strip()

        parsed = json.loads(content)
        return {
            "synthesis": parsed.get("synthesis", ""),
            "conflicts": parsed.get("conflicts", []),
            "confidence": parsed.get("confidence", "medium"),
        }

    except Exception as e:
        # Graceful degradation: don't crash the pipeline if synthesis fails
        combined = "\n\n".join(f"[{r.source_name}] {r.raw_content[:500]}" for r in valid_results)
        return {
            "synthesis": f"(Synthesis step failed: {e}. Showing raw combined content instead.)\n\n{combined}",
            "conflicts": [],
            "confidence": "low",
        }


if __name__ == "__main__":
    # Quick standalone test using fetcher.py's output
    from schema import PipelineResult
    from query_parser import parse_query
    from fetcher import fetch_all_sources

    query = "How does quantum computing affect cryptography?"
    pipeline = PipelineResult(original_query=query)
    pipeline.log_event(f"Testing synthesis for: {query}")

    sub_queries = parse_query(query)
    for sq in sub_queries[:1]:  # just test the first sub-question for speed
        sub_result = fetch_all_sources(sq, pipeline)
        synthesis = synthesize_subquery(sub_result)
        print(f"\n=== {sq} ===")
        print(f"Synthesis: {synthesis['synthesis']}")
        print(f"Conflicts: {synthesis['conflicts']}")
        print(f"Confidence: {synthesis['confidence']}")

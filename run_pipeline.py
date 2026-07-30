"""
Main Pipeline Runner
=======================
Runs the full Research Synthesis Engine end-to-end for one query:
  1. Parse the query into sub-questions (DeepSeek)
  2. Fetch from all 3 sources per sub-question, with validation (Day 2)
  3. Synthesize + cross-reference each sub-question's sources (Day 3)
  4. Generate a markdown report with provenance + confidence (Day 4)

Usage:
    python run_pipeline.py "Your research question here"
"""

import sys
from schema import PipelineResult
from query_parser import parse_query
from fetcher import fetch_all_sources
from synthesis import synthesize_subquery
from report_generator import save_report


def run_pipeline(query: str) -> PipelineResult:
    pipeline = PipelineResult(original_query=query)
    pipeline.log_event(f"=== Starting pipeline for: {query} ===")

    # Step 1: Parse
    sub_queries = parse_query(query)
    pipeline.log_event(f"Parsed into {len(sub_queries)} sub-questions.")

    # Step 2 + 3: Fetch and synthesize each sub-question
    for sq_text in sub_queries:
        sub_result = fetch_all_sources(sq_text, pipeline)

        pipeline.log_event(f"Synthesizing '{sq_text}'...")
        synthesis = synthesize_subquery(sub_result)
        sub_result.synthesis = synthesis
        pipeline.log_event(f"  -> Confidence: {synthesis['confidence']}, Conflicts found: {len(synthesis['conflicts'])}")

        pipeline.sub_query_results.append(sub_result)

    pipeline.log_event("=== Pipeline run complete ===")
    return pipeline


if __name__ == "__main__":
    query = " ".join(sys.argv[1:])
    if not query:
        print("Usage: python run_pipeline.py \"Your research question here\"")
        sys.exit(1)

    pipeline = run_pipeline(query)

    # Save both the raw JSON (for debugging/inspection) and the markdown report
    pipeline.to_json("pipeline_output.json")
    report_path = save_report(pipeline)

    print(f"\n✅ Done.")
    print(f"   JSON data: pipeline_output.json")
    print(f"   Markdown report: {report_path}")

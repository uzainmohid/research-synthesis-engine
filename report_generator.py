"""
Markdown Report Generator (Day 4)
====================================
Takes a completed PipelineResult (with synthesis already run on each
sub-query) and produces a structured markdown research report with:
  - Executive Summary
  - Key Findings (one per sub-question, with conflicts flagged)
  - Source Provenance (which info came from where)
  - Confidence Rating (per finding + overall)
  - Pipeline Log (for transparency / debugging)
"""

from datetime import datetime, timezone
from schema import PipelineResult

CONFIDENCE_EMOJI = {
    "high": "🟢 High",
    "medium": "🟡 Medium",
    "low": "🟠 Low",
    "none": "🔴 None",
}


def generate_report(pipeline: PipelineResult) -> str:
    lines = []
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines.append(f"# Research Report: {pipeline.original_query}")
    lines.append("")
    lines.append(f"*Generated {now}*")
    lines.append("")

    # ---- Executive Summary ----
    lines.append("## Executive Summary")
    lines.append("")
    summary_points = []
    for sq in pipeline.sub_query_results:
        synth_text = sq.synthesis.get("synthesis", "").strip()
        if synth_text:
            first_sentence = synth_text.split(". ")[0].rstrip(".") + "."
            summary_points.append(f"- {first_sentence}")
    if summary_points:
        lines.extend(summary_points)
    else:
        lines.append("*No synthesized findings were available to summarize.*")
    lines.append("")

    # ---- Key Findings ----
    lines.append("## Key Findings")
    lines.append("")
    for i, sq in enumerate(pipeline.sub_query_results, 1):
        confidence = sq.synthesis.get("confidence", "none")
        confidence_label = CONFIDENCE_EMOJI.get(confidence, confidence)

        lines.append(f"### {i}. {sq.sub_query}")
        lines.append("")
        lines.append(f"**Confidence:** {confidence_label}")
        lines.append("")
        lines.append(sq.synthesis.get("synthesis", "*No synthesis available.*"))
        lines.append("")

        conflicts = sq.synthesis.get("conflicts", [])
        if conflicts:
            lines.append("**⚠️ Conflicting information detected:**")
            for c in conflicts:
                lines.append(f"- {c}")
            lines.append("")

    # ---- Source Provenance ----
    lines.append("## Source Provenance")
    lines.append("")
    lines.append("| Sub-question | Source | Status | URL |")
    lines.append("|---|---|---|---|")
    for sq in pipeline.sub_query_results:
        for r in sq.source_results:
            status_icon = "✅" if r.validation_status == "valid" else "❌"
            url_display = r.url if r.url else "—"
            question_short = (sq.sub_query[:50] + "...") if len(sq.sub_query) > 50 else sq.sub_query
            lines.append(f"| {question_short} | {r.source_name} | {status_icon} {r.validation_status} | {url_display} |")
    lines.append("")

    # ---- Overall Confidence ----
    lines.append("## Overall Confidence Rating")
    lines.append("")
    confidences = [sq.synthesis.get("confidence", "none") for sq in pipeline.sub_query_results]
    score_map = {"high": 3, "medium": 2, "low": 1, "none": 0}
    avg_score = sum(score_map.get(c, 0) for c in confidences) / len(confidences) if confidences else 0
    if avg_score >= 2.5:
        overall = "🟢 High — most sub-questions had strong, agreeing multi-source data."
    elif avg_score >= 1.5:
        overall = "🟡 Medium — reasonable coverage, but some sub-questions had limited or conflicting data."
    elif avg_score >= 0.5:
        overall = "🟠 Low — significant gaps in source coverage; treat findings as preliminary."
    else:
        overall = "🔴 None — no usable data was gathered for this query."
    lines.append(overall)
    lines.append("")

    # ---- Pipeline Log (transparency) ----
    lines.append("## Pipeline Log")
    lines.append("")
    lines.append("<details>")
    lines.append("<summary>Click to expand full pipeline execution log</summary>")
    lines.append("")
    lines.append("```")
    lines.extend(pipeline.log)
    lines.append("```")
    lines.append("</details>")
    lines.append("")

    return "\n".join(lines)


def save_report(pipeline: PipelineResult, path: str = None) -> str:
    if path is None:
        safe_name = "".join(c if c.isalnum() or c == " " else "" for c in pipeline.original_query)
        safe_name = "_".join(safe_name.split())[:50]
        path = f"report_{safe_name}.md"

    report_text = generate_report(pipeline)
    with open(path, "w", encoding="utf-8") as f:
        f.write(report_text)
    return path


if __name__ == "__main__":
    # Standalone smoke test with a fake minimal pipeline result
    from schema import PipelineResult, SubQueryResult, SourceResult

    pipeline = PipelineResult(original_query="Test query for report generator")
    pipeline.log_event("Test log entry")

    sq = SubQueryResult(sub_query="Test sub-question?")
    sq.source_results.append(
        SourceResult(
            source_name="wikipedia", query="test", raw_content="Test content",
            timestamp=SourceResult.now(), validation_status="valid", url="https://example.com",
        )
    )
    sq.synthesis = {"synthesis": "This is a test synthesis.", "conflicts": [], "confidence": "medium"}
    pipeline.sub_query_results.append(sq)

    path = save_report(pipeline, "test_report.md")
    print(f"Test report saved to {path}")

"""
Pipeline Schema for the Research Synthesis Engine
====================================================
This defines the data structures that every stage of the pipeline
produces and consumes. Every source fetch MUST return a SourceResult,
whether it succeeded or failed — that's what lets the pipeline log
failures and still produce a partial report.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
import json


@dataclass
class SourceResult:
    """The result of fetching from ONE source (Wikipedia, web search, or arXiv)."""

    source_name: str          # e.g. "wikipedia", "web_search", "arxiv"
    query: str                # the sub-query sent to this source
    raw_content: str          # the actual text/data retrieved (empty string if failed)
    timestamp: str            # ISO 8601 UTC timestamp of the fetch attempt
    validation_status: str    # "valid" | "invalid" | "failed"
    validation_reason: str = ""   # why it was marked invalid/failed (empty if valid)
    url: str = ""             # source URL, if applicable
    metadata: dict = field(default_factory=dict)  # extra info (e.g. arXiv authors, publish date)

    @staticmethod
    def now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "source_name": self.source_name,
            "query": self.query,
            "raw_content": self.raw_content,
            "timestamp": self.timestamp,
            "validation_status": self.validation_status,
            "validation_reason": self.validation_reason,
            "url": self.url,
            "metadata": self.metadata,
        }


@dataclass
class SubQueryResult:
    """All source results gathered for ONE sub-question of the original query."""

    sub_query: str
    source_results: list = field(default_factory=list)  # list[SourceResult]
    synthesis: dict = field(default_factory=dict)  # {"synthesis": str, "conflicts": list, "confidence": str}

    def valid_results(self) -> list:
        return [r for r in self.source_results if r.validation_status == "valid"]

    def failed_results(self) -> list:
        return [r for r in self.source_results if r.validation_status != "valid"]


@dataclass
class PipelineResult:
    """The full result of running the pipeline end-to-end for one user query."""

    original_query: str
    sub_query_results: list = field(default_factory=list)  # list[SubQueryResult]
    log: list = field(default_factory=list)  # list of log strings, in order

    def log_event(self, message: str):
        stamped = f"[{SourceResult.now()}] {message}"
        self.log.append(stamped)
        print(stamped)  # also print live so you see progress in the terminal

    def to_json(self, path: str):
        data = {
            "original_query": self.original_query,
            "log": self.log,
            "sub_query_results": [
                {
                    "sub_query": sq.sub_query,
                    "synthesis": sq.synthesis,
                    "source_results": [r.to_dict() for r in sq.source_results],
                }
                for sq in self.sub_query_results
            ],
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

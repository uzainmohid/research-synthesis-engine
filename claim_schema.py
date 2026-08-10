"""
Claim Schema & Research Queue (Step 1 + Step 6's queue half)
================================================================
Defines the Claim data structure — the atomic unit of this whole
project. Every fact the report makes must trace back to exactly one
Claim, which carries full citation + quality info.

Also defines the ResearchQueue: a persistent JSON state file that
tracks every research question ever run (pending / in_progress /
completed), so the agent can be interrupted and resumed without
losing work, and so you can list what's been done.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import os
import uuid


@dataclass
class Claim:
    """One atomic, citable fact extracted from one source."""

    claim_text: str
    source_url: str
    source_name: str        # e.g. "wikipedia", "web_search", "arxiv", "semantic_scholar"
    source_type: str        # e.g. "encyclopedia", "general_web", "academic_paper"
    retrieved_at: str       # ISO timestamp when the source was fetched
    quality_score: float = 0.0   # filled in by quality_scorer.py, 0.0-1.0
    claim_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    sub_topic: str = ""      # which part of the question this claim addresses

    def to_dict(self) -> dict:
        return {
            "claim_id": self.claim_id,
            "claim_text": self.claim_text,
            "source_url": self.source_url,
            "source_name": self.source_name,
            "source_type": self.source_type,
            "retrieved_at": self.retrieved_at,
            "quality_score": self.quality_score,
            "sub_topic": self.sub_topic,
        }

    @staticmethod
    def from_dict(d: dict) -> "Claim":
        return Claim(
            claim_text=d["claim_text"],
            source_url=d["source_url"],
            source_name=d["source_name"],
            source_type=d["source_type"],
            retrieved_at=d["retrieved_at"],
            quality_score=d.get("quality_score", 0.0),
            claim_id=d.get("claim_id", uuid.uuid4().hex[:8]),
            sub_topic=d.get("sub_topic", ""),
        )


class ResearchQueue:
    """Persistent JSON-backed queue of research questions and their status.
    Lets the agent handle multiple questions across sessions without
    losing track of what's pending, in progress, or completed."""

    def __init__(self, path: str = "research_queue.json"):
        self.path = path
        self.entries = self._load()

    def _load(self) -> list:
        if not os.path.exists(self.path):
            return []
        with open(self.path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.entries, f, indent=2, ensure_ascii=False)

    def add_question(self, question: str) -> str:
        """Adds a new pending question. Returns its entry id."""
        entry_id = uuid.uuid4().hex[:8]
        self.entries.append({
            "id": entry_id,
            "question": question,
            "status": "pending",
            "report_path": None,
            "claims_path": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": None,
        })
        self._save()
        return entry_id

    def mark_in_progress(self, entry_id: str):
        self._update(entry_id, status="in_progress")

    def mark_completed(self, entry_id: str, report_path: str, claims_path: str):
        self._update(
            entry_id,
            status="completed",
            report_path=report_path,
            claims_path=claims_path,
            completed_at=datetime.now(timezone.utc).isoformat(),
        )

    def mark_failed(self, entry_id: str, reason: str):
        self._update(entry_id, status="failed", failure_reason=reason)

    def _update(self, entry_id: str, **fields):
        for entry in self.entries:
            if entry["id"] == entry_id:
                entry.update(fields)
                break
        self._save()

    def list_pending(self) -> list:
        return [e for e in self.entries if e["status"] in ("pending", "in_progress")]

    def list_completed(self) -> list:
        return [e for e in self.entries if e["status"] == "completed"]

    def print_status(self):
        pending = self.list_pending()
        completed = self.list_completed()
        print(f"\n=== Research Queue: {len(self.entries)} total ===")
        print(f"\nPending / In Progress ({len(pending)}):")
        for e in pending:
            print(f"  [{e['id']}] {e['question']}  ({e['status']})")
        print(f"\nCompleted ({len(completed)}):")
        for e in completed:
            print(f"  [{e['id']}] {e['question']}")
            print(f"      report: {e['report_path']}")


if __name__ == "__main__":
    # Quick smoke test
    q = ResearchQueue("test_queue.json")
    eid = q.add_question("Test question?")
    q.mark_in_progress(eid)
    q.mark_completed(eid, "report_test.docx", "claims_test.json")
    q.print_status()

"""
M38I–M38L: Persist adaptation candidates, quarantine state, and review decisions.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.safe_adaptation.models import (
    AdaptationCandidate,
    AdaptationEvidenceBundle,
    QuarantineState,
    ReviewDecision,
    ADAPTATION_STATUS_PENDING,
    ADAPTATION_STATUS_QUARANTINED,
)


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


ADAPTATION_DIR = "data/local/safe_adaptation"
CANDIDATES_DIR = "candidates"
QUARANTINE_FILE = "quarantine.jsonl"
DECISIONS_FILE = "decisions.jsonl"


def _adaptation_root(repo_root: Path | str | None) -> Path:
    return _root(repo_root) / ADAPTATION_DIR


def _candidate_path(adaptation_id: str, repo_root: Path | str | None) -> Path:
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in (adaptation_id or "").strip())
    return _adaptation_root(repo_root) / CANDIDATES_DIR / f"{safe}.json"


def _decisions_path(repo_root: Path | str | None) -> Path:
    return _adaptation_root(repo_root) / DECISIONS_FILE


def _quarantine_path(repo_root: Path | str | None) -> Path:
    return _adaptation_root(repo_root) / QUARANTINE_FILE


def _dict_to_evidence(d: dict[str, Any]) -> AdaptationEvidenceBundle:
    return AdaptationEvidenceBundle(
        evidence_ids=d.get("evidence_ids", []),
        correction_ids=d.get("correction_ids", []),
        session_ids=d.get("session_ids", []),
        summary=d.get("summary", ""),
        evidence_count=d.get("evidence_count", 0),
    )


def save_candidate(candidate: AdaptationCandidate, repo_root: Path | str | None = None) -> Path:
    """Write candidate to candidates/<adaptation_id>.json."""
    root = _adaptation_root(repo_root)
    (root / CANDIDATES_DIR).mkdir(parents=True, exist_ok=True)
    path = _candidate_path(candidate.adaptation_id, repo_root)
    path.write_text(json.dumps(candidate.to_dict(), indent=2), encoding="utf-8")
    return path


def load_candidate(adaptation_id: str, repo_root: Path | str | None = None) -> AdaptationCandidate | None:
    """Load one candidate by id."""
    path = _candidate_path(adaptation_id, repo_root)
    if not path.exists() or not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        ev = data.get("evidence", {})
        return AdaptationCandidate(
            adaptation_id=data.get("adaptation_id", ""),
            cohort_id=data.get("cohort_id", ""),
            affected_surface_ids=data.get("affected_surface_ids", []),
            surface_type=data.get("surface_type", "experimental"),
            target_type=data.get("target_type", ""),
            target_id=data.get("target_id", ""),
            before_value=data.get("before_value"),
            after_value=data.get("after_value"),
            evidence=_dict_to_evidence(ev) if isinstance(ev, dict) else ev,
            risk_level=data.get("risk_level", "low"),
            review_status=data.get("review_status", ADAPTATION_STATUS_PENDING),
            created_at_utc=data.get("created_at_utc", ""),
            updated_at_utc=data.get("updated_at_utc", ""),
            summary=data.get("summary", ""),
            extra=data.get("extra", {}),
        )
    except Exception:
        return None


def list_candidates(
    repo_root: Path | str | None = None,
    cohort_id: str = "",
    review_status: str = "",
    limit: int = 50,
) -> list[AdaptationCandidate]:
    """List candidates newest first; optional filter by cohort_id and review_status."""
    root = _adaptation_root(repo_root) / CANDIDATES_DIR
    if not root.exists():
        return []
    out: list[AdaptationCandidate] = []
    for path in sorted(root.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        if not path.is_file() or path.suffix != ".json":
            continue
        c = load_candidate(path.stem, repo_root)
        if not c:
            continue
        if cohort_id and c.cohort_id != cohort_id:
            continue
        if review_status and c.review_status != review_status:
            continue
        out.append(c)
        if len(out) >= limit:
            break
    return out


def update_review_status(
    adaptation_id: str,
    review_status: str,
    repo_root: Path | str | None = None,
) -> bool:
    """Update candidate review_status; returns True if updated."""
    c = load_candidate(adaptation_id, repo_root)
    if not c:
        return False
    c.review_status = review_status
    try:
        from workflow_dataset.utils.dates import utc_now_iso
    except Exception:
        from datetime import datetime, timezone
        def utc_now_iso() -> str:
            return datetime.now(timezone.utc).isoformat()
    c.updated_at_utc = utc_now_iso()
    save_candidate(c, repo_root)
    return True


def append_quarantine(state: QuarantineState, repo_root: Path | str | None = None) -> Path:
    """Append one quarantine record (JSONL)."""
    path = _quarantine_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(state.to_dict()) + "\n")
    return path


def list_quarantined(
    repo_root: Path | str | None = None,
    limit: int = 50,
) -> list[QuarantineState]:
    """Load quarantine records (newest last in file = reverse order)."""
    path = _quarantine_path(repo_root)
    if not path.exists():
        return []
    lines: list[str] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                lines.append(line)
    out: list[QuarantineState] = []
    for line in reversed(lines[-limit:]):
        try:
            d = json.loads(line)
            out.append(QuarantineState(
                candidate_id=d.get("candidate_id", ""),
                reason=d.get("reason", ""),
                quarantined_at_utc=d.get("quarantined_at_utc", ""),
                review_recommended_by_utc=d.get("review_recommended_by_utc", ""),
                notes=d.get("notes", ""),
            ))
        except Exception:
            continue
    return out[:limit]


def append_decision(decision: ReviewDecision, repo_root: Path | str | None = None) -> Path:
    """Append one review decision (JSONL)."""
    path = _decisions_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(decision.to_dict()) + "\n")
    return path


def list_recent_decisions(
    repo_root: Path | str | None = None,
    candidate_id: str = "",
    decision: str = "",
    limit: int = 30,
) -> list[ReviewDecision]:
    """List recent decisions (newest last); optional filter by candidate_id and decision."""
    path = _decisions_path(repo_root)
    if not path.exists():
        return []
    lines: list[str] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                lines.append(line)
    out: list[ReviewDecision] = []
    for line in reversed(lines[-limit * 2:]):
        try:
            d = json.loads(line)
            if candidate_id and d.get("candidate_id") != candidate_id:
                continue
            if decision and d.get("decision") != decision:
                continue
            out.append(ReviewDecision(
                decision_id=d.get("decision_id", ""),
                candidate_id=d.get("candidate_id", ""),
                decision=d.get("decision", ""),
                rationale=d.get("rationale", ""),
                behavior_delta_summary=d.get("behavior_delta_summary", ""),
                reviewed_at_utc=d.get("reviewed_at_utc", ""),
                reviewed_by=d.get("reviewed_by", ""),
            ))
            if len(out) >= limit:
                break
        except Exception:
            continue
    return out

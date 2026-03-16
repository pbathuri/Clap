"""
M23O: Digest history — persist and compare daily digest snapshots.
Local-only; data/local/context/digests/.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

from workflow_dataset.daily.inbox import DailyDigest, build_daily_digest


def _repo_root(root: Path | str | None) -> Path:
    if root is not None:
        return Path(root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return get_repo_root().resolve()
    except Exception:
        return Path.cwd().resolve()


DIGESTS_DIR_NAME = "digests"
LATEST_DIGEST_NAME = "latest.json"
PREVIOUS_DIGEST_NAME = "previous.json"


def get_digests_dir(repo_root: Path | str | None = None) -> Path:
    from workflow_dataset.context.config import get_context_root
    d = get_context_root(repo_root) / DIGESTS_DIR_NAME
    d.mkdir(parents=True, exist_ok=True)
    return d


def _digest_to_dict(d: DailyDigest) -> dict[str, Any]:
    return {
        "created_at": d.created_at,
        "work_state_snapshot_id": d.work_state_snapshot_id,
        "what_changed": list(d.what_changed),
        "relevant_job_ids": list(d.relevant_job_ids),
        "relevant_routine_ids": list(d.relevant_routine_ids),
        "blocked_items": list(d.blocked_items),
        "reminders_due_count": len(d.reminders_due),
        "approvals_needing_refresh": list(d.approvals_needing_refresh),
        "trust_regressions": list(d.trust_regressions),
        "recent_successful_runs_count": len(d.recent_successful_runs),
        "recommended_next_action": d.recommended_next_action,
        "top_next_recommended": dict(d.top_next_recommended),
        "unresolved_corrections_count": d.unresolved_corrections_count,
        "corrections_review_recommended": list(d.corrections_review_recommended),
        "inbox_item_ids": [x.get("id") for x in d.inbox_items if x.get("id")],
    }


def _digest_from_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Return a minimal dict for compare; not full DailyDigest."""
    return data


def save_digest_snapshot(
    digest: DailyDigest,
    repo_root: Path | str | None = None,
    snapshot_id: str | None = None,
) -> Path:
    """Persist digest to data/local/context/digests/. Optional timestamped file; always update latest.json and previous.json."""
    root = _repo_root(repo_root)
    digests_dir = get_digests_dir(root)
    sid = snapshot_id or (digest.created_at or utc_now_iso()).replace(":", "").replace("-", "")[:14]
    data = _digest_to_dict(digest)
    data["snapshot_id"] = sid
    latest_path = digests_dir / LATEST_DIGEST_NAME
    previous_path = digests_dir / PREVIOUS_DIGEST_NAME
    if latest_path.exists():
        previous_path.write_text(latest_path.read_text(encoding="utf-8"), encoding="utf-8")
    latest_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    ts_path = digests_dir / f"digest_{sid}.json"
    ts_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return ts_path


def load_digest_snapshot(
    snapshot_id: str = "latest",
    repo_root: Path | str | None = None,
) -> dict[str, Any] | None:
    """Load digest snapshot by id ('latest', 'previous', or timestamp id). Returns dict (not full DailyDigest)."""
    digests_dir = get_digests_dir(repo_root)
    if snapshot_id == "latest":
        path = digests_dir / LATEST_DIGEST_NAME
    elif snapshot_id == "previous":
        path = digests_dir / PREVIOUS_DIGEST_NAME
    else:
        path = digests_dir / f"digest_{snapshot_id}.json"
    if not path.exists() or not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def list_digest_snapshots(
    limit: int = 20,
    repo_root: Path | str | None = None,
) -> list[dict[str, Any]]:
    """List digest snapshot ids and created_at (newest first)."""
    digests_dir = get_digests_dir(repo_root)
    out = []
    for f in sorted(digests_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        if not f.is_file() or f.suffix != ".json" or not f.name.startswith("digest_") or f.name in (LATEST_DIGEST_NAME, PREVIOUS_DIGEST_NAME):
            continue
        sid = f.stem.replace("digest_", "")
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            out.append({"snapshot_id": sid, "created_at": data.get("created_at", "")})
        except Exception:
            out.append({"snapshot_id": sid, "created_at": ""})
        if len(out) >= limit:
            break
    return out


@dataclass
class DigestCompare:
    """What changed between two digest snapshots."""
    newly_appeared: list[str] = field(default_factory=list)  # item ids in newer not in older
    dropped: list[str] = field(default_factory=list)  # item ids in older not in newer
    escalated: list[str] = field(default_factory=list)  # was blocked in older, not in newer (or became top)
    summary: list[str] = field(default_factory=list)


def compare_digests(
    older: dict[str, Any],
    newer: dict[str, Any],
) -> DigestCompare:
    """Compare two digest snapshots (dicts from load_digest_snapshot). Returns DigestCompare."""
    result = DigestCompare()
    old_ids = set(older.get("inbox_item_ids") or [])
    new_ids = set(newer.get("inbox_item_ids") or [])
    result.newly_appeared = sorted(new_ids - old_ids)
    result.dropped = sorted(old_ids - new_ids)
    old_blocked = {b.get("id") for b in (older.get("blocked_items") or []) if b.get("id")}
    new_blocked = {b.get("id") for b in (newer.get("blocked_items") or []) if b.get("id")}
    result.escalated = sorted(old_blocked - new_blocked)
    if result.newly_appeared:
        result.summary.append(f"Newly appeared: {', '.join(result.newly_appeared[:10])}")
    if result.dropped:
        result.summary.append(f"Dropped: {', '.join(result.dropped[:10])}")
    if result.escalated:
        result.summary.append(f"No longer blocked: {', '.join(result.escalated[:10])}")
    if not result.summary:
        result.summary.append("No significant change between snapshots.")
    return result

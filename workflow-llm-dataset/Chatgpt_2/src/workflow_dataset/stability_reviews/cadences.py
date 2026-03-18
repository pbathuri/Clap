"""
M46L.1: Review cadences — daily, weekly, rolling stability review; next due date.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from workflow_dataset.stability_reviews.models import ReviewCadence


# Built-in cadences
DEFAULT_CADENCES: list[ReviewCadence] = [
    ReviewCadence(
        cadence_id="daily",
        kind="daily",
        window_kind="daily",
        label="Daily stability review",
        description="Review every 24h; window = last 24h.",
        default_days_until_next=1,
    ),
    ReviewCadence(
        cadence_id="weekly",
        kind="weekly",
        window_kind="weekly",
        label="Weekly stability review",
        description="Review every 7 days; window = last 7 days.",
        default_days_until_next=7,
    ),
    ReviewCadence(
        cadence_id="rolling_stability",
        kind="rolling_stability",
        window_kind="rolling_7",
        label="Rolling stability review (7d)",
        description="Rolling 7-day window; review on a weekly cadence.",
        default_days_until_next=7,
    ),
]


def get_default_cadences() -> list[ReviewCadence]:
    """Return built-in review cadences."""
    return list(DEFAULT_CADENCES)


def get_cadence_for(cadence_id: str) -> ReviewCadence | None:
    """Return the cadence with the given id, or None."""
    for c in DEFAULT_CADENCES:
        if c.cadence_id == cadence_id:
            return c
    return None


def next_review_due_iso(
    cadence: ReviewCadence,
    last_review_at_iso: str | None = None,
    from_iso: str | None = None,
) -> str:
    """
    Compute next scheduled review time (ISO) from cadence and last review (or from_iso).
    If last_review_at_iso is None, use from_iso or now plus default_days_until_next.
    """
    now = datetime.now(timezone.utc)
    base = now
    if from_iso:
        try:
            base = datetime.fromisoformat(from_iso.replace("Z", "+00:00"))
        except Exception:
            pass
    elif last_review_at_iso:
        try:
            base = datetime.fromisoformat(last_review_at_iso.replace("Z", "+00:00"))
        except Exception:
            pass
    delta = timedelta(days=cadence.default_days_until_next)
    next_dt = base + delta
    return next_dt.isoformat()[:19] + "Z"


def load_active_cadence(repo_root: Path | str | None = None) -> ReviewCadence:
    """Load active cadence from store, or return default rolling_stability."""
    root = _repo_root(repo_root)
    path = root / "data/local/stability_reviews/cadence.json"
    if path.exists():
        try:
            import json
            data = json.loads(path.read_text(encoding="utf-8"))
            cid = data.get("cadence_id", "rolling_stability")
            cadence = get_cadence_for(cid)
            if cadence:
                return cadence
        except Exception:
            pass
    return get_cadence_for("rolling_stability") or DEFAULT_CADENCES[-1]


def save_active_cadence(
    cadence_id: str,
    repo_root: Path | str | None = None,
) -> Path:
    """Persist active cadence id. Returns path to cadence.json."""
    root = _repo_root(repo_root)
    d = root / "data/local/stability_reviews"
    d.mkdir(parents=True, exist_ok=True)
    path = d / "cadence.json"
    import json
    path.write_text(
        json.dumps({"cadence_id": cadence_id, "updated_at_iso": _now_iso()}, indent=2),
        encoding="utf-8",
    )
    return path


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()[:19] + "Z"

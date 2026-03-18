"""
M37H.1: Interruption budgets (per hour / per day).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

from workflow_dataset.signal_quality.models import InterruptionBudget


BUDGETS_DIR = "data/local/signal_quality"
BUDGET_FILE = "interruption_budget.json"


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _budget_path(repo_root: Path | str | None) -> Path:
    return _root(repo_root) / BUDGETS_DIR / BUDGET_FILE


def _parse_window_start(window_start_utc: str, period_hours: float) -> bool:
    """True if window has expired (should reset)."""
    if not window_start_utc:
        return True
    try:
        from datetime import datetime, timezone, timedelta
        start = datetime.fromisoformat(window_start_utc.replace("Z", "+00:00"))
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        return (now - start).total_seconds() >= period_hours * 3600
    except Exception:
        return True


def get_or_create_budget(
    repo_root: Path | str | None = None,
    period_hours: float = 1.0,
    max_interruptions: int = 15,
) -> InterruptionBudget:
    """Load budget from disk or create default; reset window if expired."""
    path = _budget_path(repo_root)
    now = utc_now_iso()
    default = InterruptionBudget(
        budget_id="per_hour" if period_hours <= 1.0 else "per_day",
        period_hours=period_hours,
        max_interruptions=max_interruptions,
        consumed=0,
        window_start_utc=now,
    )
    if not path.exists():
        return default
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        budget = InterruptionBudget(
            budget_id=data.get("budget_id", default.budget_id),
            period_hours=float(data.get("period_hours", period_hours)),
            max_interruptions=int(data.get("max_interruptions", max_interruptions)),
            consumed=int(data.get("consumed", 0)),
            window_start_utc=data.get("window_start_utc", now),
        )
        if _parse_window_start(budget.window_start_utc, budget.period_hours):
            budget.consumed = 0
            budget.window_start_utc = now
        return budget
    except Exception:
        return default


def save_budget(budget: InterruptionBudget, repo_root: Path | str | None = None) -> Path:
    """Persist budget to disk."""
    path = _budget_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(budget.model_dump_json(indent=2), encoding="utf-8")
    return path


def consume_one(repo_root: Path | str | None = None) -> InterruptionBudget:
    """Increment consumed for current window; reset if window expired. Returns updated budget."""
    budget = get_or_create_budget(repo_root)
    budget.consumed = budget.consumed + 1
    save_budget(budget, repo_root)
    return budget


def remaining(repo_root: Path | str | None = None) -> int:
    """Remaining interruptions in current window."""
    budget = get_or_create_budget(repo_root)
    return max(0, budget.max_interruptions - budget.consumed)


def build_interruption_budget_report(repo_root: Path | str | None = None) -> dict[str, Any]:
    """Report: budget status, remaining, window start, recommendation."""
    budget = get_or_create_budget(repo_root)
    rem = remaining(repo_root)
    return {
        "budget_id": budget.budget_id,
        "period_hours": budget.period_hours,
        "max_interruptions": budget.max_interruptions,
        "consumed": budget.consumed,
        "remaining": rem,
        "window_start_utc": budget.window_start_utc,
        "recommendation": "Under budget; interruptions allowed." if rem > 0 else "Budget exhausted for this window; consider digest or quiet mode.",
    }

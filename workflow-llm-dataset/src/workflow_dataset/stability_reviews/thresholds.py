"""
M46L.1: Operator-facing thresholds — when to continue as-is vs watch vs narrow vs pause.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.stability_reviews.models import StabilityThresholds


DEFAULT_THRESHOLDS = StabilityThresholds(
    thresholds_id="default",
    label="Default operator thresholds",
    max_warnings_continue_as_is=0,
    max_triage_issues_continue_as_is=0,
    require_checkpoint_criteria_for_continue=False,
    min_triage_issues_narrow=1,
    min_warnings_narrow=3,
    min_blockers_pause=1,
    min_failed_gates_pause=1,
    use_watch_when_weak_evidence=True,
    use_watch_when_warnings_in_band=True,
    description="Continue as-is only with no warnings/triage issues; watch when weak or in band; narrow at 1+ triage or 3+ warnings; pause at 1+ blocker or failed gate.",
)


def get_default_thresholds() -> StabilityThresholds:
    return DEFAULT_THRESHOLDS


def load_thresholds(repo_root: Path | str | None = None) -> StabilityThresholds:
    """Load thresholds from store, or return default."""
    root = _repo_root(repo_root)
    path = root / "data/local/stability_reviews/thresholds.json"
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return _thresholds_from_dict(data)
        except Exception:
            pass
    return get_default_thresholds()


def save_thresholds(
    thresholds: StabilityThresholds,
    repo_root: Path | str | None = None,
) -> Path:
    """Persist thresholds. Returns path to thresholds.json."""
    root = _repo_root(repo_root)
    d = root / "data/local/stability_reviews"
    d.mkdir(parents=True, exist_ok=True)
    path = d / "thresholds.json"
    path.write_text(json.dumps(thresholds.to_dict(), indent=2), encoding="utf-8")
    return path


def apply_thresholds(
    thresholds: StabilityThresholds,
    *,
    blocker_count: int,
    warning_count: int,
    failed_gates_count: int,
    triage_issues: int,
    checkpoint_criteria_met: bool,
    health_summary_has_signals: bool,
) -> dict[str, Any]:
    """
    Map evidence to operator-facing bands: continue_as_is | continue_with_watch | narrow | pause.
    Returns dict with: band, reason, overrides_continue, overrides_watch, overrides_narrow, overrides_pause.
    Does not override guidance/launch rollback/repair; use for continue vs watch vs narrow vs pause only.
    """
    out: dict[str, Any] = {
        "band": "continue_as_is",
        "reason": "",
        "overrides_continue": False,
        "overrides_watch": False,
        "overrides_narrow": False,
        "overrides_pause": False,
    }
    if blocker_count >= thresholds.min_blockers_pause or failed_gates_count >= thresholds.min_failed_gates_pause:
        out["band"] = "pause"
        out["reason"] = f"Blockers={blocker_count} or failed_gates={failed_gates_count} meet pause threshold."
        out["overrides_pause"] = True
        return out
    if triage_issues >= thresholds.min_triage_issues_narrow or warning_count >= thresholds.min_warnings_narrow:
        out["band"] = "narrow"
        out["reason"] = f"Triage issues={triage_issues} or warnings={warning_count} meet narrow threshold."
        out["overrides_narrow"] = True
        return out
    if thresholds.require_checkpoint_criteria_for_continue and not checkpoint_criteria_met:
        out["band"] = "continue_with_watch"
        out["reason"] = "Checkpoint criteria not met; use watch."
        out["overrides_watch"] = True
        return out
    if warning_count > thresholds.max_warnings_continue_as_is or triage_issues > thresholds.max_triage_issues_continue_as_is:
        out["band"] = "continue_with_watch"
        out["reason"] = f"Warnings={warning_count} or triage_issues={triage_issues} exceed continue-as-is limit."
        out["overrides_watch"] = True
        return out
    if thresholds.use_watch_when_weak_evidence and not health_summary_has_signals:
        out["band"] = "continue_with_watch"
        out["reason"] = "Weak evidence; use watch."
        out["overrides_watch"] = True
        return out
    if thresholds.use_watch_when_warnings_in_band and 0 < warning_count <= thresholds.min_warnings_narrow:
        out["band"] = "continue_with_watch"
        out["reason"] = "Warnings in band; use watch."
        out["overrides_watch"] = True
        return out
    out["reason"] = "Within thresholds for continue as-is."
    out["overrides_continue"] = True
    return out


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _thresholds_from_dict(data: dict[str, Any]) -> StabilityThresholds:
    return StabilityThresholds(
        thresholds_id=data.get("thresholds_id", "default"),
        label=data.get("label", ""),
        max_warnings_continue_as_is=data.get("max_warnings_continue_as_is", 0),
        max_triage_issues_continue_as_is=data.get("max_triage_issues_continue_as_is", 0),
        require_checkpoint_criteria_for_continue=data.get("require_checkpoint_criteria_for_continue", False),
        min_triage_issues_narrow=data.get("min_triage_issues_narrow", 1),
        min_warnings_narrow=data.get("min_warnings_narrow", 3),
        min_blockers_pause=data.get("min_blockers_pause", 1),
        min_failed_gates_pause=data.get("min_failed_gates_pause", 1),
        use_watch_when_weak_evidence=data.get("use_watch_when_weak_evidence", True),
        use_watch_when_warnings_in_band=data.get("use_watch_when_warnings_in_band", True),
        description=data.get("description", ""),
    )

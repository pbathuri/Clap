"""
M37L.1: State compaction recommendations — archival targets, operator-facing recommendations.
Read-only; no archival without explicit operator action.
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

try:
    from workflow_dataset.utils.hashes import stable_id
except Exception:
    def stable_id(*parts: str, prefix: str = "") -> str:
        import hashlib
        return prefix + hashlib.sha256("".join(str(p) for p in parts).encode()).hexdigest()[:14]

from workflow_dataset.state_durability.models import (
    ArchivalTarget,
    CompactionRecommendation,
    CompactionRecommendationOutput,
)
from workflow_dataset.state_durability.profiles import get_maintenance_profile


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _count_and_oldest_utc(entries: list[dict[str, Any]], ts_key: str = "timestamp") -> tuple[int, str]:
    """Return (len(entries), oldest_utc)."""
    if not entries:
        return 0, ""
    oldest = ""
    for e in entries:
        ts = e.get(ts_key) or e.get("created_at") or e.get("saved_at") or ""
        if ts and (not oldest or ts < oldest):
            oldest = ts
    return len(entries), oldest


def _gather_background_run_target(root: Path) -> ArchivalTarget | None:
    """Gather background_run history count and oldest; return ArchivalTarget or None."""
    path = root / "data/local/background_run/history.json"
    if not path.exists():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        entries = raw.get("entries", [])
    except Exception:
        return None
    count, oldest = _count_and_oldest_utc(entries)
    return ArchivalTarget(
        subsystem_id="background_run",
        scope="background_run_history",
        path_or_location="data/local/background_run/history.json",
        item_count=count,
        oldest_utc=oldest,
        retain_days_recommended=30,
    )


def _gather_automation_inbox_target(root: Path) -> ArchivalTarget | None:
    """Gather automation_inbox decision/store count if available."""
    path = root / "data/local/automation_inbox"
    if not path.exists() or not path.is_dir():
        return None
    count = 0
    oldest = ""
    decisions_file = path / "decisions.json"
    if decisions_file.exists():
        try:
            raw = json.loads(decisions_file.read_text(encoding="utf-8"))
            entries = raw.get("decisions", raw.get("entries", []))
            if isinstance(entries, dict):
                entries = list(entries.values()) if entries else []
            count, oldest = _count_and_oldest_utc(entries, "decided_at")
        except Exception:
            pass
    return ArchivalTarget(
        subsystem_id="automation_inbox",
        scope="automation_inbox_decisions",
        path_or_location="data/local/automation_inbox",
        item_count=count,
        oldest_utc=oldest,
        retain_days_recommended=14,
    )


def _gather_event_log_target(root: Path) -> ArchivalTarget | None:
    """Gather event_log/timeline approximate count if dir exists."""
    event_dir = root / "data/local/event_log"
    if not event_dir.exists() or not event_dir.is_dir():
        return None
    count = 0
    try:
        for f in event_dir.iterdir():
            if f.is_file() and f.suffix in (".json", ".jsonl"):
                count += 1
    except Exception:
        pass
    return ArchivalTarget(
        subsystem_id="event_log",
        scope="event_log",
        path_or_location="data/local/event_log",
        item_count=count,
        oldest_utc="",
        retain_days_recommended=30,
    )


def build_compaction_recommendations(
    repo_root: Path | str | None = None,
    profile_id: str = "balanced",
) -> CompactionRecommendationOutput:
    """Build compaction recommendations from current state and maintenance profile. Read-only."""
    root = _root(repo_root)
    now = utc_now_iso()
    profile = get_maintenance_profile(profile_id)
    targets: list[ArchivalTarget] = []
    recommendations: list[CompactionRecommendation] = []
    operator_lines: list[str] = []

    # Gather targets
    for gather in [_gather_background_run_target, _gather_automation_inbox_target, _gather_event_log_target]:
        t = gather(root)
        if t and (t.item_count > 0 or t.path_or_location):
            targets.append(t)

    policy_by_subsystem = {p.subsystem_id: p for p in profile.policies}

    for target in targets:
        policy = policy_by_subsystem.get(target.subsystem_id)
        retain_days = policy.retain_days if policy else target.retain_days_recommended
        max_items = policy.max_items_before_summarize if policy else 200

        rec_id = stable_id("comp", target.subsystem_id, target.scope, now[:10], prefix="rec_")
        suggest_summarize = target.item_count >= max_items if max_items else False
        action_kind = "summarize" if suggest_summarize else "review_only"
        summary = f"{target.subsystem_id} ({target.scope}): {target.item_count} item(s)."
        if suggest_summarize:
            summary += f" Above threshold {max_items}; consider summarization or archival."
        suggested_cmd = "workflow-dataset state compaction-recommendations"
        if target.subsystem_id == "background_run":
            suggested_cmd = "workflow-dataset background history (review); no auto-archival."
        elif target.subsystem_id == "automation_inbox":
            suggested_cmd = "workflow-dataset automation-inbox list (review); decisions kept for audit."

        recommendations.append(CompactionRecommendation(
            recommendation_id=rec_id,
            subsystem_id=target.subsystem_id,
            scope=target.scope,
            operator_summary=summary,
            action_kind=action_kind,
            item_count=target.item_count,
            suggested_command=suggested_cmd,
            safe_to_apply=True,
        ))
        operator_lines.append(summary)

    if not operator_lines:
        operator_lines.append("No compaction targets above threshold. State is within profile limits.")

    return CompactionRecommendationOutput(
        generated_at_utc=now,
        profile_id=profile.profile_id,
        profile_label=profile.label,
        archival_targets=targets,
        recommendations=recommendations,
        operator_summary_lines=operator_lines,
    )

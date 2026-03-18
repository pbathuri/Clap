"""
M36I–M36L: Continuity engine store — last session end, last shutdown, carry-forward, next-session recommendation.
Data: data/local/continuity_engine/.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.continuity_engine.models import (
    ShutdownSummary,
    CarryForwardItem,
    NextSessionRecommendation,
    DailyRhythmTemplate,
    RhythmPhase,
)


CONTINUITY_DIR = "data/local/continuity_engine"
LAST_SESSION_FILE = "last_session.json"
LAST_SHUTDOWN_FILE = "last_shutdown.json"
CARRY_FORWARD_FILE = "carry_forward.json"
NEXT_SESSION_FILE = "next_session.json"
# M36L.1
RHYTHM_TEMPLATES_FILE = "rhythm_templates.json"
ACTIVE_RHYTHM_TEMPLATE_FILE = "active_rhythm_template_id.txt"


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def get_continuity_dir(repo_root: Path | str | None = None) -> Path:
    return _repo_root(repo_root) / CONTINUITY_DIR


def get_last_session_end_utc(repo_root: Path | str | None = None) -> str:
    """Return last session end timestamp (from last_session.json or last shutdown)."""
    root = get_continuity_dir(repo_root)
    path = root / LAST_SESSION_FILE
    if not path.exists():
        # Fallback: from last shutdown
        shut = load_last_shutdown(repo_root)
        if shut:
            return shut.generated_at_utc or ""
        return ""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return str(raw.get("last_session_end_utc", ""))
    except Exception:
        return ""


def save_last_session_end(last_session_end_utc: str, repo_root: Path | str | None = None) -> Path:
    root = get_continuity_dir(repo_root)
    root.mkdir(parents=True, exist_ok=True)
    path = root / LAST_SESSION_FILE
    path.write_text(json.dumps({"last_session_end_utc": last_session_end_utc}, indent=2), encoding="utf-8")
    return path


def load_last_shutdown(repo_root: Path | str | None = None) -> ShutdownSummary | None:
    path = get_continuity_dir(repo_root) / LAST_SHUTDOWN_FILE
    if not path.exists():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return _shutdown_from_dict(raw)
    except Exception:
        return None


def save_last_shutdown(summary: ShutdownSummary, repo_root: Path | str | None = None) -> Path:
    root = get_continuity_dir(repo_root)
    root.mkdir(parents=True, exist_ok=True)
    path = root / LAST_SHUTDOWN_FILE
    path.write_text(json.dumps(summary.to_dict(), indent=2), encoding="utf-8")
    return path


def _shutdown_from_dict(d: dict[str, Any]) -> ShutdownSummary:
    return ShutdownSummary(
        summary_id=d.get("summary_id", ""),
        generated_at_utc=d.get("generated_at_utc", ""),
        day_id=d.get("day_id", ""),
        completed_work=list(d.get("completed_work") or []),
        unresolved_items=list(d.get("unresolved_items") or []),
        carry_forward_items=list(d.get("carry_forward_items") or []),
        tomorrow_likely_start=d.get("tomorrow_likely_start", ""),
        tomorrow_first_action=d.get("tomorrow_first_action", ""),
        blocked_or_high_risk=list(d.get("blocked_or_high_risk") or []),
        end_of_day_readiness=d.get("end_of_day_readiness", ""),
    )


def load_carry_forward(repo_root: Path | str | None = None) -> list[CarryForwardItem]:
    path = get_continuity_dir(repo_root) / CARRY_FORWARD_FILE
    if not path.exists():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        items = raw.get("items", [])
        return [CarryForwardItem(
            item_id=str(i.get("item_id", "")),
            kind=str(i.get("kind", "")),
            carry_forward_class=str(i.get("carry_forward_class", "")),
            label=str(i.get("label", "")),
            detail=str(i.get("detail", "")),
            ref=str(i.get("ref", "")),
            command=str(i.get("command", "")),
            created_at_utc=str(i.get("created_at_utc", "")),
            priority=str(i.get("priority", "medium")),
        ) for i in items]
    except Exception:
        return []


def save_carry_forward(items: list[CarryForwardItem], repo_root: Path | str | None = None) -> Path:
    root = get_continuity_dir(repo_root)
    root.mkdir(parents=True, exist_ok=True)
    path = root / CARRY_FORWARD_FILE
    path.write_text(json.dumps({"items": [i.to_dict() for i in items]}, indent=2), encoding="utf-8")
    return path


def load_next_session_recommendation(repo_root: Path | str | None = None) -> NextSessionRecommendation | None:
    path = get_continuity_dir(repo_root) / NEXT_SESSION_FILE
    if not path.exists():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return NextSessionRecommendation(
            generated_at_utc=raw.get("generated_at_utc", ""),
            day_id=raw.get("day_id", ""),
            likely_start_context=raw.get("likely_start_context", ""),
            first_action_label=raw.get("first_action_label", ""),
            first_action_command=raw.get("first_action_command", ""),
            carry_forward_count=int(raw.get("carry_forward_count", 0)),
            blocked_count=int(raw.get("blocked_count", 0)),
            urgent_carry_forward_count=int(raw.get("urgent_carry_forward_count", 0)),
            optional_carry_forward_count=int(raw.get("optional_carry_forward_count", 0)),
            automated_follow_up_count=int(raw.get("automated_follow_up_count", 0)),
            operating_mode=raw.get("operating_mode", ""),
            rationale_lines=list(raw.get("rationale_lines") or []),
            memory_context=dict(raw.get("memory_context") or {}),
        )
    except Exception:
        return None


def save_next_session_recommendation(rec: NextSessionRecommendation, repo_root: Path | str | None = None) -> Path:
    root = get_continuity_dir(repo_root)
    root.mkdir(parents=True, exist_ok=True)
    path = root / NEXT_SESSION_FILE
    path.write_text(json.dumps(rec.to_dict(), indent=2), encoding="utf-8")
    return path


# ---------- M36L.1 Daily rhythm templates ----------


def load_rhythm_templates(repo_root: Path | str | None = None) -> list[DailyRhythmTemplate]:
    """Load rhythm templates from JSON; if missing, return built-in defaults."""
    root = get_continuity_dir(repo_root)
    path = root / RHYTHM_TEMPLATES_FILE
    if path.exists():
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            templates = raw.get("templates", [])
            return [DailyRhythmTemplate.from_dict(t) for t in templates]
        except Exception:
            pass
    return _default_rhythm_templates()


def save_rhythm_templates(
    templates: list[DailyRhythmTemplate], repo_root: Path | str | None = None
) -> Path:
    root = get_continuity_dir(repo_root)
    root.mkdir(parents=True, exist_ok=True)
    path = root / RHYTHM_TEMPLATES_FILE
    path.write_text(
        json.dumps({"templates": [t.to_dict() for t in templates]}, indent=2), encoding="utf-8"
    )
    return path


def _default_rhythm_templates() -> list[DailyRhythmTemplate]:
    """Built-in default daily rhythm templates."""
    default_phases = [
        RhythmPhase("morning_check", "Morning check", 15, "workflow-dataset continuity morning", 0),
        RhythmPhase("inbox_review", "Inbox & approvals", 20, "workflow-dataset inbox list", 1),
        RhythmPhase("deep_work", "Deep work", 90, "workflow-dataset workspace open", 2),
        RhythmPhase("review", "Review & queue", 30, "workflow-dataset queue view", 3),
        RhythmPhase("wrap_up", "Wrap-up", 15, "workflow-dataset continuity shutdown", 4),
    ]
    return [
        DailyRhythmTemplate(
            template_id="default",
            name="Default day",
            description="Morning check → inbox → deep work → review → wrap-up",
            phases=default_phases,
            default_first_phase_id="morning_check",
        ),
    ]


def get_active_rhythm_template_id(repo_root: Path | str | None = None) -> str:
    path = get_continuity_dir(repo_root) / ACTIVE_RHYTHM_TEMPLATE_FILE
    if not path.exists():
        return "default"
    try:
        return path.read_text(encoding="utf-8").strip() or "default"
    except Exception:
        return "default"


def set_active_rhythm_template_id(template_id: str, repo_root: Path | str | None = None) -> Path:
    root = get_continuity_dir(repo_root)
    root.mkdir(parents=True, exist_ok=True)
    path = root / ACTIVE_RHYTHM_TEMPLATE_FILE
    path.write_text(template_id.strip(), encoding="utf-8")
    return path

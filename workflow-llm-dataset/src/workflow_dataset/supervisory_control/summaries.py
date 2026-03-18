"""
M45L.1: Operator-facing summaries — when to continue, intervene, or terminate; suggested playbook.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.supervisory_control.models import OperatorLoopSummary
from workflow_dataset.supervisory_control.store import (
    load_current_preset_id,
    load_pause_state,
    load_takeover_state,
    load_interventions,
)
from workflow_dataset.supervisory_control.panel import inspect_loop, inspect_confidence_gates, get_loop
from workflow_dataset.supervisory_control.presets import (
    get_preset_by_id,
    get_default_presets,
    get_playbook_by_id,
    get_playbooks_for_trigger,
    get_default_playbooks,
)
from workflow_dataset.supervisory_control.presets import (
    PLAYBOOK_BLOCKED_NO_PROGRESS,
    PLAYBOOK_REPEATED_HANDOFF_FAILURE,
    PLAYBOOK_PENDING_STALE,
    PLAYBOOK_HIGH_RISK_PENDING,
)

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def build_operator_summary(
    loop_id: str,
    repo_root: Path | str | None = None,
    preset_id: str = "",
) -> OperatorLoopSummary:
    """
    Build operator-facing summary: when to continue, intervene, or terminate;
    attach preset hints and suggest a playbook if the loop matches a trigger.
    """
    root = _root(repo_root)
    pid = preset_id or load_current_preset_id(repo_root)
    preset = get_preset_by_id(pid)
    if not preset:
        # Fallback to first default
        presets = get_default_presets()
        preset = presets[0] if presets else None
    view = get_loop(loop_id, repo_root)
    gates = inspect_confidence_gates(loop_id, repo_root)
    pause = load_pause_state(loop_id, repo_root)
    takeover = load_takeover_state(loop_id, repo_root)
    interventions = [i for i in load_interventions(repo_root) if i.loop_id == loop_id]

    continue_rec = preset.when_to_continue_hint if preset else "Review loop status and approve next step if appropriate."
    intervene_rec = preset.when_to_intervene_hint if preset else "Pause or redirect when the loop is stuck or you need to correct course."
    terminate_rec = preset.when_to_terminate_hint if preset else "Stop the loop when the goal is obsolete or the plan is invalid."

    suggested_playbook_id = ""
    suggested_playbook_label = ""

    # Match trigger conditions
    blocked = (gates.get("blocked_reason") or "").strip()
    pending_count = gates.get("pending_approval_count", 0) or (view.pending_count if view else 0)
    cycle_status = gates.get("cycle_status", "")
    failure_count = sum(1 for i in interventions if i.kind in ("takeover", "stop") or (i.payload.get("error") if isinstance(i.payload, dict) else False))

    if blocked or cycle_status == "blocked":
        pb = get_playbook_by_id(PLAYBOOK_BLOCKED_NO_PROGRESS)
        if pb:
            suggested_playbook_id = pb.playbook_id
            suggested_playbook_label = pb.label
            continue_rec = pb.when_to_continue
            intervene_rec = pb.when_to_intervene
            terminate_rec = pb.when_to_terminate
    elif preset and preset.max_pending_before_escalation > 0 and pending_count >= preset.max_pending_before_escalation:
        pb = get_playbook_by_id(PLAYBOOK_PENDING_STALE)
        if pb:
            suggested_playbook_id = pb.playbook_id
            suggested_playbook_label = pb.label
            continue_rec = pb.when_to_continue
            intervene_rec = pb.when_to_intervene
            terminate_rec = pb.when_to_terminate
    elif preset and preset.suggest_takeover_on_repeated_failure and failure_count >= preset.repeated_failure_count:
        pb = get_playbook_by_id(PLAYBOOK_REPEATED_HANDOFF_FAILURE)
        if pb:
            suggested_playbook_id = pb.playbook_id
            suggested_playbook_label = pb.label
            continue_rec = pb.when_to_continue
            intervene_rec = pb.when_to_intervene
            terminate_rec = pb.when_to_terminate

    return OperatorLoopSummary(
        loop_id=loop_id,
        continue_recommendation=continue_rec,
        intervene_recommendation=intervene_rec,
        terminate_recommendation=terminate_rec,
        suggested_playbook_id=suggested_playbook_id,
        suggested_playbook_label=suggested_playbook_label,
        preset_id=pid,
        created_at_utc=utc_now_iso(),
    )


def list_presets_with_current(repo_root: Path | str | None = None) -> tuple[list[dict[str, Any]], str]:
    """Return (presets as dict, current_preset_id). Uses stored presets or defaults."""
    from workflow_dataset.supervisory_control.store import load_supervision_presets
    stored = load_supervision_presets(repo_root)
    presets = [p.to_dict() for p in stored] if stored else [p.to_dict() for p in get_default_presets()]
    current = load_current_preset_id(repo_root)
    return presets, current


def list_playbooks(repo_root: Path | str | None = None) -> list[dict[str, Any]]:
    """Return playbooks as dict; stored or defaults."""
    from workflow_dataset.supervisory_control.store import load_takeover_playbooks
    stored = load_takeover_playbooks(repo_root)
    if stored:
        return [p.to_dict() for p in stored]
    return [p.to_dict() for p in get_default_playbooks()]

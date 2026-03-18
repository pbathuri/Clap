"""
M47B–M47C: First-value stage assessment, friction points, ambiguity points, blocked cases.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.vertical_excellence.models import (
    AmbiguityPoint,
    FrictionPoint,
    FirstValuePathStage,
)
from workflow_dataset.vertical_excellence.path_resolver import (
    build_first_value_path_for_vertical,
    get_chosen_vertical_id,
)


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def assess_first_value_stage(repo_root: Path | str | None = None) -> FirstValuePathStage:
    """
    Assess current first-value path stage for the chosen vertical.
    Uses vertical_packs progress when available; else infers from step 0 (not started).
    """
    root = _root(repo_root)
    vertical_id = get_chosen_vertical_id(root)
    path = build_first_value_path_for_vertical(vertical_id, root)
    if path is None:
        return FirstValuePathStage(
            vertical_id=vertical_id,
            step_index=0,
            total_steps=0,
            status="not_started",
            next_command_hint="workflow-dataset production-cut lock --id <vertical_id> or workflow-dataset value-packs first-run --id " + vertical_id,
        )
    steps = getattr(path, "steps", []) or []
    total = len(steps)
    next_hint = path.entry_point if path else "workflow-dataset package first-run"
    try:
        from workflow_dataset.vertical_packs.store import get_path_progress
        progress = get_path_progress(root)
        if progress.get("pack_id") == vertical_id and progress.get("path_id"):
            reached = progress.get("reached_milestone_ids", [])
            blocked = progress.get("blocked_step_index", 0)
            next_milestone = progress.get("next_milestone_id", "")
            first_value_mid = getattr(path, "first_value_milestone_id", "") or "first_simulate_done"
            if first_value_mid in reached:
                return FirstValuePathStage(
                    vertical_id=vertical_id,
                    step_index=total,
                    total_steps=total,
                    status="first_value_reached",
                    milestone_id=first_value_mid,
                    next_command_hint=path.suggested_next_actions[0] if getattr(path, "suggested_next_actions", None) else "workflow-dataset day status",
                )
            step_index = blocked if blocked > 0 else min(len(reached) + 1, total)
            if step_index <= 0:
                step_index = 1
            next_step = steps[step_index - 1] if 1 <= step_index <= len(steps) else None
            if next_step:
                next_hint = getattr(next_step, "command", next_hint)
            return FirstValuePathStage(
                vertical_id=vertical_id,
                step_index=step_index,
                total_steps=total,
                status="blocked" if blocked > 0 else "in_progress",
                milestone_id=next_milestone,
                next_command_hint=next_hint,
            )
    except Exception:
        pass
    if total > 0 and hasattr(steps[0], "command"):
        next_hint = steps[0].command
    return FirstValuePathStage(
        vertical_id=vertical_id,
        step_index=0,
        total_steps=total,
        status="not_started",
        next_command_hint=next_hint,
    )


def list_friction_points(repo_root: Path | str | None = None) -> list[FrictionPoint]:
    """
    List friction points for the chosen vertical: from common_failure_points on first-value path
    and from vertical_speed friction clusters.
    """
    root = _root(repo_root)
    vertical_id = get_chosen_vertical_id(root)
    out: list[FrictionPoint] = []
    path = build_first_value_path_for_vertical(vertical_id, root)
    if path and getattr(path, "common_failure_points", None):
        for fp in path.common_failure_points:
            out.append(FrictionPoint(
                friction_id=f"failure_step_{fp.step_index}",
                kind="blocked_recovery",
                step_index=fp.step_index,
                label=fp.symptom or "Failure at step",
                remediation_hint=fp.remediation_hint or "",
                escalation_command=fp.escalation_command or "",
            ))
    try:
        from workflow_dataset.vertical_speed.friction import build_friction_clusters
        clusters = build_friction_clusters(root)
        for c in clusters:
            out.append(FrictionPoint(
                friction_id=c.cluster_id,
                kind=getattr(c.kind, "value", str(c.kind)),
                step_index=0,
                label=c.label or "",
                remediation_hint=c.suggested_action or c.impact_summary or "",
                escalation_command="",
            ))
    except Exception:
        pass
    return out


def list_ambiguity_points(repo_root: Path | str | None = None) -> list[AmbiguityPoint]:
    """
    List ambiguity points: steps where "what to do next" may be unclear.
    Derived from first-value path steps that have no or weak what_to_do_next.
    """
    root = _root(repo_root)
    vertical_id = get_chosen_vertical_id(root)
    path = build_first_value_path_for_vertical(vertical_id, root)
    out: list[AmbiguityPoint] = []
    if path is None:
        out.append(AmbiguityPoint(
            ambiguity_id="no_path",
            step_index=0,
            label="No first-value path for this vertical",
            suggested_next="workflow-dataset value-packs first-run --id " + vertical_id,
        ))
        return out
    steps = getattr(path, "steps", []) or []
    for i, s in enumerate(steps):
        step_num = i + 1
        next_hint = getattr(s, "what_to_do_next", "") or getattr(s, "command", "")
        if not next_hint or len(next_hint) < 3:
            out.append(AmbiguityPoint(
                ambiguity_id=f"step_{step_num}_unclear",
                step_index=step_num,
                label=getattr(s, "title", f"Step {step_num}") + " — next step unclear",
                suggested_next=getattr(s, "command", "workflow-dataset day status"),
            ))
    return out


def list_blocked_first_value_cases(repo_root: Path | str | None = None) -> list[dict[str, Any]]:
    """
    List blocked first-value cases: progress says blocked at step N, or no active vertical/project.
    """
    root = _root(repo_root)
    cases: list[dict[str, Any]] = []
    vertical_id = get_chosen_vertical_id(root)
    if not vertical_id:
        cases.append({"reason": "no_active_vertical", "step_index": 0, "hint": "workflow-dataset production-cut lock --id <vertical_id>"})
        return cases
    try:
        from workflow_dataset.vertical_packs.store import get_path_progress
        progress = get_path_progress(root)
        blocked = progress.get("blocked_step_index", 0)
        if blocked > 0 and progress.get("pack_id") == vertical_id:
            path = build_first_value_path_for_vertical(vertical_id, root)
            remediation = ""
            if path and getattr(path, "common_failure_points", None):
                for fp in path.common_failure_points:
                    if fp.step_index == blocked:
                        remediation = fp.remediation_hint or fp.escalation_command
                        break
            cases.append({
                "reason": "blocked_at_step",
                "step_index": blocked,
                "hint": remediation or "workflow-dataset vertical-excellence recommend-next",
            })
    except Exception:
        pass
    return cases

"""
M29: Unified home / overview — format workspace home for CLI. Phase C.
M29D.1: Preset-aware formatting (section order, role-specific quick actions).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.workspace.state import build_workspace_home_snapshot
from workflow_dataset.workspace.models import (
    WorkspaceHomeSnapshot,
    HOME_SECTION_WHERE,
    HOME_SECTION_TOP_PRIORITY,
    HOME_SECTION_APPROVALS,
    HOME_SECTION_BLOCKED,
    HOME_SECTION_RECENT,
    HOME_SECTION_TRUST_HEALTH,
    HOME_SECTION_AREAS,
    HOME_SECTION_QUICK,
    HOME_SECTIONS_DEFAULT,
)
from workflow_dataset.workspace.presets import get_preset


def build_unified_home(
    repo_root: Path | str | None = None,
    preset_id: str | None = None,
) -> WorkspaceHomeSnapshot:
    """Build unified home snapshot (delegate to state). Preset does not change snapshot data."""
    return build_workspace_home_snapshot(repo_root)


def format_workspace_home(
    snapshot: WorkspaceHomeSnapshot | None = None,
    repo_root: Path | str | None = None,
    preset_id: str | None = None,
) -> str:
    """Format workspace home for CLI. If preset_id is set, use preset section order and quick actions (M29D.1)."""
    if snapshot is None:
        snapshot = build_workspace_home_snapshot(repo_root)
    preset = get_preset(preset_id) if preset_id else None
    section_order = tuple(preset.home_section_order) if preset and preset.home_section_order else HOME_SECTIONS_DEFAULT

    # Build section chunks (id -> list of lines)
    def where_lines() -> list[str]:
        return [
            "[Where you are]",
            f"  Project: {snapshot.context.active_project_id or '—'}  {snapshot.context.active_project_title or ''}",
            f"  Session: {snapshot.context.active_session_id or '—'}  pack: {snapshot.context.active_session_pack_id or '—'}",
            f"  Goal: {(snapshot.context.active_goal_text[:60] + '…') if snapshot.context.active_goal_text else '—'}",
        ]

    def top_priority_lines() -> list[str]:
        return [
            "[Top priority / Next]",
            f"  Next project: {snapshot.top_priority_project_id or snapshot.context.next_recommended_project_id or '—'}",
            f"  Reason: {snapshot.context.portfolio_next_reason or '—'}",
            f"  Next action: {snapshot.context.next_recommended_action or 'hold'}  — {(snapshot.context.next_recommended_detail or '')[:80]}",
        ]

    def approvals_lines() -> list[str]:
        return ["[Approvals]", f"  {snapshot.approval_queue_summary}"]

    def blocked_lines() -> list[str]:
        return ["[Blocked]", f"  {snapshot.blocked_summary}"]

    def recent_lines() -> list[str]:
        return [
            "[Recent]",
            f"  {snapshot.recent_activity_summary}",
            f"  Artifacts: {snapshot.context.recent_artifacts_count}",
        ]

    def trust_health_lines() -> list[str]:
        return ["[Trust / Health]", f"  {snapshot.trust_health_summary}"]

    def areas_lines() -> list[str]:
        out = ["[Areas]"]
        for a in snapshot.areas:
            count_str = f"  ({a.count})" if a.count else ""
            out.append(f"  {a.area_id}: {a.label}{count_str}  — {a.command_hint}")
        return out

    def quick_lines() -> list[str]:
        if preset and preset.default_quick_actions:
            parts = [f"  {q['label']}: {q['command']}" for q in preset.default_quick_actions]
            return ["[Quick]", ""] + parts
        return [
            "[Quick]  workflow-dataset workspace context  |  workflow-dataset workspace next  |  workflow-dataset mission-control"
        ]

    sections = {
        HOME_SECTION_WHERE: where_lines,
        HOME_SECTION_TOP_PRIORITY: top_priority_lines,
        HOME_SECTION_APPROVALS: approvals_lines,
        HOME_SECTION_BLOCKED: blocked_lines,
        HOME_SECTION_RECENT: recent_lines,
        HOME_SECTION_TRUST_HEALTH: trust_health_lines,
        HOME_SECTION_AREAS: areas_lines,
        HOME_SECTION_QUICK: quick_lines,
    }

    lines = ["=== Workspace Home ===", ""]
    if preset:
        lines.append(f"(Preset: {preset.label})")
        lines.append(f"  Recommended first view: {preset.recommended_first_view}")
        lines.append("")
    for sec_id in section_order:
        if sec_id in sections:
            lines.extend(sections[sec_id]())
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"

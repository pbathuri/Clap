"""
M24: Multi-pack status and conflict reporting.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.packs.pack_registry import list_installed_packs, get_installed_manifest
from workflow_dataset.packs.pack_activation import (
    load_activation_state,
    get_primary_pack_id,
    get_pinned,
    get_suspended_pack_ids,
    get_current_context,
)
from workflow_dataset.packs.pack_resolution_graph import resolve_with_priority
from workflow_dataset.packs.pack_conflicts import detect_conflicts, ConflictClass
from workflow_dataset.packs.pack_state import get_packs_dir


def write_multi_pack_status_report(
    packs_dir: Path | str | None = None,
    output_path: Path | str | None = None,
) -> Path:
    """Write multi_pack_status_report.md summarizing installed packs, active graph, role/context."""
    root = Path(packs_dir) if packs_dir else get_packs_dir()
    out = Path(output_path) if output_path else root / "multi_pack_status_report.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    state = load_activation_state(packs_dir)
    installed = list_installed_packs(packs_dir)
    primary = get_primary_pack_id(packs_dir)
    pinned = get_pinned(packs_dir)
    suspended = get_suspended_pack_ids(packs_dir)
    ctx = get_current_context(packs_dir)
    cap, expl = resolve_with_priority(
        role=ctx.get("current_role"),
        workflow_type=ctx.get("current_workflow"),
        task_type=ctx.get("current_task"),
        packs_dir=packs_dir,
    )
    lines = [
        "# Multi-pack status report",
        "",
        "## Installed packs",
        "",
    ]
    for rec in installed:
        lines.append(f"- {rec.get('pack_id')} @ {rec.get('version')}")
    lines.extend([
        "",
        "## Activation state",
        "",
        f"- **Primary pack:** {primary or '(none)'}",
        f"- **Pinned:** {pinned or '(none)'}",
        f"- **Suspended:** {suspended or '(none)'}",
        f"- **Current role:** {ctx.get('current_role') or '(none)'}",
        f"- **Current workflow:** {ctx.get('current_workflow') or '(none)'}",
        f"- **Current task:** {ctx.get('current_task') or '(none)'}",
        "",
        "## Active capability resolution",
        "",
        f"- **Summary:** {expl.summary}",
        f"- **Active packs:** {[m.pack_id for m in cap.active_packs]}",
        f"- **Templates:** {cap.templates}",
        f"- **Output adapters:** {cap.output_adapters}",
        "",
        "## Role/context switching",
        "",
        "- Use `workflow-dataset runtime switch-role <role>` to set current role.",
        "- Use `workflow-dataset runtime switch-context --workflow W --task T` to set context.",
        "- Use `workflow-dataset runtime clear-context` to clear role/workflow/task and pins.",
        "",
    ])
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def write_conflict_report(
    packs_dir: Path | str | None = None,
    role: str | None = None,
    workflow: str | None = None,
    task: str | None = None,
    output_path: Path | str | None = None,
) -> Path:
    """Write conflict_report.md listing detected conflicts and resolution."""
    root = Path(packs_dir) if packs_dir else get_packs_dir()
    out = Path(output_path) if output_path else root / "conflict_report.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    installed = list_installed_packs(packs_dir)
    manifests = []
    for rec in installed:
        m = get_installed_manifest(rec["pack_id"], packs_dir)
        if m:
            manifests.append(m)
    conflicts = detect_conflicts(manifests, role=role, workflow=workflow, task=task)
    lines = [
        "# Pack conflict report",
        "",
        f"**Scope:** role={role or '(any)'} workflow={workflow or '(any)'} task={task or '(any)'}",
        "",
        "## Conflicts",
        "",
    ]
    if not conflicts:
        lines.append("No conflicts detected.")
        lines.append("")
    else:
        by_class: dict[str, list[Any]] = {}
        for c in conflicts:
            by_class.setdefault(c.conflict_class.value, []).append(c)
        for cls in [ConflictClass.BLOCKED.value, ConflictClass.INCOMPATIBLE.value, ConflictClass.PRECEDENCE_REQUIRED.value, ConflictClass.MERGEABLE.value, ConflictClass.HARMLESS_OVERLAP.value]:
            for c in by_class.get(cls, []):
                lines.append(f"### [{c.conflict_class.value}] {c.capability}")
                lines.append("")
                lines.append(f"- **Packs:** {c.pack_ids}")
                lines.append(f"- **Description:** {c.description}")
                lines.append(f"- **Resolution:** {c.resolution}")
                lines.append("")
    lines.append("## Precedence rules")
    lines.append("")
    lines.append("- Primary pack wins for role scope (templates, default adapter, retrieval).")
    lines.append("- Pinned pack wins for its scope (session/project/task).")
    lines.append("- Safety constraints merge conservatively (stricter wins).")
    lines.append("- Blocked conflicts: strict local-only wins; wrapper pack excluded when strict is primary.")
    lines.append("")
    out.write_text("\n".join(lines), encoding="utf-8")
    return out

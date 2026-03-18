"""
M27D: Project/case report formatting — list, show, goals, report.
"""

from __future__ import annotations

from workflow_dataset.project_case.store import load_project, get_linked_sessions, get_linked_plans, get_linked_runs, get_linked_artifacts
from workflow_dataset.project_case.goal_stack import list_goals, list_subgoals, get_blocked_goals, recommended_next_goal
from workflow_dataset.project_case.graph import get_project_summary


def format_project_list(projects: list[dict], current_id: str | None = None) -> str:
    """Format list of projects for CLI."""
    lines = ["=== Projects ===", ""]
    for p in projects:
        cur = " (current)" if p.get("project_id") == current_id else ""
        lines.append(f"  {p.get('project_id', '')}  {p.get('title', '')}  state={p.get('state', '')}{cur}")
    if not projects:
        lines.append("  (none; create with: workflow-dataset projects create --id <id>)")
    return "\n".join(lines)


def format_project_show(project_id: str, repo_root=None) -> str:
    """Format single project show."""
    proj = load_project(project_id, repo_root)
    if not proj:
        return f"Project not found: {project_id}"
    lines = [
        f"project_id: {proj.project_id}",
        f"title: {proj.title}",
        f"description: {proj.description or '—'}",
        f"state: {proj.state}",
        f"created_at: {proj.created_at}",
        f"updated_at: {proj.updated_at}",
    ]
    sessions = get_linked_sessions(project_id, repo_root)
    plans = get_linked_plans(project_id, repo_root)
    runs = get_linked_runs(project_id, repo_root)
    artifacts = get_linked_artifacts(project_id, repo_root)
    lines.append(f"linked_sessions: {[s.session_id for s in sessions]}")
    lines.append(f"linked_plans: {len(plans)}")
    lines.append(f"linked_runs: {[r.run_id for r in runs]}")
    lines.append(f"linked_artifacts: {len(artifacts)}")
    return "\n".join(lines)


def format_goal_stack(project_id: str, repo_root=None) -> str:
    """Format goal stack (ordered goals with status)."""
    proj = load_project(project_id, repo_root)
    if not proj:
        return f"Project not found: {project_id}"
    goals = list_goals(project_id, repo_root)
    lines = [f"=== Goal stack: {project_id} ===", ""]
    for g in goals:
        subgoals = list_subgoals(project_id, g.goal_id, repo_root)
        sub_str = f"  ({len(subgoals)} subgoals)" if subgoals else ""
        lines.append(f"  [{g.order}] {g.goal_id}  {g.title or '—'}  status={g.status}{sub_str}")
        if g.blocked_reason:
            lines.append(f"      blocked: {g.blocked_reason}")
    if not goals:
        lines.append("  (no goals; add with: workflow-dataset projects goals --id <id> --add <goal_id> --title '...')")
    return "\n".join(lines)


def format_project_report(project_id: str, repo_root=None) -> str:
    """Format full project report: summary, blockers, next action, linked items."""
    summary = get_project_summary(project_id, repo_root)
    if summary.get("error"):
        return summary["error"]
    lines = [
        f"=== Project report: {summary.get('title', project_id)} ===",
        "",
        f"state: {summary.get('state', '')}",
        f"goals: {summary.get('goals_count', 0)}  (active/blocked/deferred/complete in project_state)",
        "",
    ]
    blocked = summary.get("blocked_goals", [])
    if blocked:
        lines.append("Blocked goals:")
        for b in blocked:
            lines.append(f"  - {b.get('goal_id')}: {b.get('reason', '')}")
        lines.append("")
    next_action = summary.get("recommended_next_action")
    if next_action:
        lines.append(f"Recommended next: {next_action.get('action_type')} — {next_action.get('label')} ({next_action.get('reason', '')})")
        lines.append("")
    latest = summary.get("latest_linked", {})
    if any(latest.values()):
        lines.append("Latest linked:")
        if latest.get("session_id"):
            lines.append(f"  session: {latest['session_id']}")
        if latest.get("run_id"):
            lines.append(f"  run: {latest['run_id']}")
        if latest.get("plan_id"):
            lines.append(f"  plan: {latest['plan_id']}")
        if latest.get("artifact"):
            lines.append(f"  artifact: {latest['artifact']}")
    return "\n".join(lines)


# ----- M27D.1 Template / goal archetype formatting -----


def format_template_list(templates: list) -> str:
    """Format list of project templates for CLI."""
    lines = ["=== Project templates ===", ""]
    for t in templates:
        lines.append(f"  {t.template_id}  {t.title or t.template_id}")
    if not templates:
        lines.append("  (no templates)")
    return "\n".join(lines)


def format_goal_archetype(template_id: str, repo_root=None) -> str:
    """Format one template's goal archetype (default goal stack + artifacts, blockers, packs). M27D.1."""
    from workflow_dataset.project_case.templates import get_template
    t = get_template(template_id, repo_root)
    if not t:
        return f"Template not found: {template_id}"
    lines = [
        f"=== Goal archetype: {t.template_id} ===",
        "",
        f"title: {t.title}",
        f"description: {t.description or '—'}",
        "",
        "Default goal stack:",
    ]
    for g in t.default_goal_stack:
        block = f"  (default blocked: {g.default_blocked_reason})" if g.default_blocked_reason else ""
        lines.append(f"  [{g.order}] {g.goal_id}  {g.title or '—'}{block}")
    lines.append("")
    lines.append("Common artifacts: " + ", ".join(t.common_artifacts) if t.common_artifacts else "Common artifacts: (none)")
    lines.append("Likely blockers: " + ", ".join(t.likely_blockers) if t.likely_blockers else "Likely blockers: (none)")
    lines.append("Recommended packs: " + ", ".join(t.recommended_pack_ids) if t.recommended_pack_ids else "Recommended packs: (none)")
    lines.append("Recommended value-packs: " + ", ".join(t.recommended_value_pack_ids) if t.recommended_value_pack_ids else "Recommended value-packs: (none)")
    return "\n".join(lines)

"""
M23L: Local work-state model. Snapshot of current working context from local sources only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()


@dataclass
class WorkState:
    """Current work context derived from local inspectable sources."""
    snapshot_id: str = ""
    created_at: str = ""
    # Job context
    recent_successful_jobs: list[dict] = field(default_factory=list)  # [{job_pack_id, run_id, timestamp}]
    trusted_for_real_jobs: list[str] = field(default_factory=list)
    approval_blocked_jobs: list[str] = field(default_factory=list)
    simulate_only_jobs: list[str] = field(default_factory=list)
    jobs_with_failure_notes: list[str] = field(default_factory=list)
    # Intake
    intake_labels: list[str] = field(default_factory=list)
    intake_summary: list[dict] = field(default_factory=list)  # [{label, file_count, created_at}]
    # Workspace / package / review
    recent_workspaces_count: int = 0
    unreviewed_count: int = 0
    package_pending_count: int = 0
    recent_workspaces_sample: list[dict] = field(default_factory=list)
    # Approvals / capabilities
    approvals_file_exists: bool = False
    approved_paths_count: int = 0
    approved_action_scopes_count: int = 0
    adapter_ids: list[str] = field(default_factory=list)
    # Copilot
    reminders_count: int = 0
    reminders_due_sample: list[dict] = field(default_factory=list)
    routines_count: int = 0
    routine_ids: list[str] = field(default_factory=list)
    recent_plan_runs_count: int = 0
    recent_plan_runs_sample: list[dict] = field(default_factory=list)
    # Task demos
    task_demos_count: int = 0
    # Errors (per-source)
    errors: dict[str, str] = field(default_factory=dict)


def build_work_state(repo_root: Path | str | None = None) -> WorkState:
    """
    Build current work-state snapshot from local sources only.
    No network; read-only from job_packs, intake, dashboard, approvals, copilot, task_demos.
    """
    root = Path(repo_root).resolve() if repo_root else None
    state = WorkState(
        snapshot_id="",
        created_at=utc_now_iso(),
    )

    # Job packs report
    try:
        from workflow_dataset.job_packs import job_packs_report
        report = job_packs_report(root)
        state.recent_successful_jobs = list(report.get("recent_successful", []))[:20]
        state.trusted_for_real_jobs = list(report.get("trusted_for_real_jobs", []))
        state.approval_blocked_jobs = list(report.get("approval_blocked_jobs", []))
        state.simulate_only_jobs = list(report.get("simulate_only_jobs", []))
        state.jobs_with_failure_notes = list(report.get("jobs_with_failure_notes", []))
    except Exception as e:
        state.errors["job_packs"] = str(e)

    # Intake
    try:
        from workflow_dataset.intake.registry import list_intakes
        intakes = list_intakes(root)
        state.intake_summary = [
            {"label": i.get("label"), "file_count": i.get("file_count", 0), "created_at": i.get("created_at")}
            for i in intakes
        ]
        state.intake_labels = [i.get("label") for i in intakes if i.get("label")]
    except Exception as e:
        state.errors["intake"] = str(e)

    # Dashboard: recent workspaces, review/package
    try:
        from workflow_dataset.release.dashboard_data import get_dashboard_data
        dash = get_dashboard_data(repo_root=root)
        state.recent_workspaces_count = len(dash.get("recent_workspaces", []))
        rp = dash.get("review_package", {})
        state.unreviewed_count = rp.get("unreviewed_count", 0)
        state.package_pending_count = rp.get("package_pending_count", 0)
        state.recent_workspaces_sample = list(dash.get("recent_workspaces", []))[:5]
    except Exception as e:
        state.errors["dashboard"] = str(e)

    # Approvals / capabilities
    try:
        from workflow_dataset.capability_discovery.approval_registry import get_registry_path, load_approval_registry
        from workflow_dataset.desktop_adapters.registry import list_adapters
        reg_path = get_registry_path(root)
        state.approvals_file_exists = reg_path.exists() and reg_path.is_file()
        registry = load_approval_registry(root) if state.approvals_file_exists else None
        if registry:
            state.approved_paths_count = len(registry.approved_paths)
            state.approved_action_scopes_count = len(registry.approved_action_scopes)
        adapters = list_adapters()
        state.adapter_ids = [a.adapter_id for a in adapters]
    except Exception as e:
        state.errors["approvals"] = str(e)

    # Copilot: reminders, routines, plan runs
    try:
        from workflow_dataset.copilot.reminders import list_reminders, reminders_due
        from workflow_dataset.copilot.routines import list_routines
        from workflow_dataset.copilot.run import list_plan_runs
        state.reminders_count = len(list_reminders(root))
        state.reminders_due_sample = list(reminders_due(root, limit=5))
        state.routine_ids = list_routines(root)
        state.routines_count = len(state.routine_ids)
        runs = list_plan_runs(limit=5, repo_root=root)
        state.recent_plan_runs_count = len(runs)
        state.recent_plan_runs_sample = [
            {"run_id": r.get("run_id"), "plan_id": r.get("plan_id"), "mode": r.get("mode"), "executed": len(r.get("executed", []))}
            for r in runs
        ]
    except Exception as e:
        state.errors["copilot"] = str(e)

    # Task demos
    try:
        from workflow_dataset.task_demos.store import list_tasks
        state.task_demos_count = len(list_tasks(root))
    except Exception as e:
        state.errors["task_demos"] = str(e)

    return state


def work_state_to_dict(ws: WorkState) -> dict[str, Any]:
    """Serializable dict for JSON persistence."""
    return {
        "snapshot_id": ws.snapshot_id,
        "created_at": ws.created_at,
        "recent_successful_jobs": ws.recent_successful_jobs,
        "trusted_for_real_jobs": ws.trusted_for_real_jobs,
        "approval_blocked_jobs": ws.approval_blocked_jobs,
        "simulate_only_jobs": ws.simulate_only_jobs,
        "jobs_with_failure_notes": ws.jobs_with_failure_notes,
        "intake_labels": ws.intake_labels,
        "intake_summary": ws.intake_summary,
        "recent_workspaces_count": ws.recent_workspaces_count,
        "unreviewed_count": ws.unreviewed_count,
        "package_pending_count": ws.package_pending_count,
        "recent_workspaces_sample": ws.recent_workspaces_sample,
        "approvals_file_exists": ws.approvals_file_exists,
        "approved_paths_count": ws.approved_paths_count,
        "approved_action_scopes_count": ws.approved_action_scopes_count,
        "adapter_ids": ws.adapter_ids,
        "reminders_count": ws.reminders_count,
        "reminders_due_sample": ws.reminders_due_sample,
        "routines_count": ws.routines_count,
        "routine_ids": ws.routine_ids,
        "recent_plan_runs_count": ws.recent_plan_runs_count,
        "recent_plan_runs_sample": ws.recent_plan_runs_sample,
        "task_demos_count": ws.task_demos_count,
        "errors": ws.errors,
    }


def work_state_summary_md(ws: WorkState) -> str:
    """Human-readable summary for work_state_summary.md."""
    lines = [
        "# Work state summary",
        "",
        f"Snapshot: {ws.snapshot_id or 'in-memory'}  Created: {ws.created_at}",
        "",
        "## Jobs",
        f"- Recent successful: {len(ws.recent_successful_jobs)}",
        f"- Trusted for real: {len(ws.trusted_for_real_jobs)}",
        f"- Approval blocked: {len(ws.approval_blocked_jobs)}",
        f"- Simulate only: {len(ws.simulate_only_jobs)}",
        "",
        "## Intake",
        f"- Labels: {', '.join(ws.intake_labels) or '—'}",
        "",
        "## Workspace / review",
        f"- Recent workspaces: {ws.recent_workspaces_count}  Unreviewed: {ws.unreviewed_count}  Package pending: {ws.package_pending_count}",
        "",
        "## Approvals",
        f"- Registry present: {ws.approvals_file_exists}  Paths: {ws.approved_paths_count}  Scopes: {ws.approved_action_scopes_count}",
        "",
        "## Copilot",
        f"- Reminders: {ws.reminders_count}  Routines: {ws.routines_count}  Recent plan runs: {ws.recent_plan_runs_count}",
        "",
        "## Task demos",
        f"- Count: {ws.task_demos_count}",
        "",
    ]
    if ws.errors:
        lines.append("## Errors")
        for k, v in ws.errors.items():
            lines.append(f"- {k}: {v}")
        lines.append("")
    return "\n".join(lines)

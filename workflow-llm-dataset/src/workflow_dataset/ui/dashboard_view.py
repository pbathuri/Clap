"""
M21U: Local Reporting Command Center — unified dashboard view.
Readiness, recent workspaces, review/package queue, cohort, next actions.
C4: Action shortcuts / operator macros (command only or console trigger).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from workflow_dataset.settings import Settings
from workflow_dataset.ui.models import Screen
from workflow_dataset.ui.state_store import ConsoleState


def _render_alert_strip(console: Console, data: dict) -> None:
    """C3: Single-line alert strip: review pending, package ready, staged apply-plan, benchmark regression."""
    alerts = data.get("alerts") or {}
    parts: list[str] = []
    if alerts.get("review_pending"):
        n = alerts.get("review_pending_count", 0)
        parts.append(f"[yellow]Review pending: {n}[/yellow]")
    if alerts.get("package_ready"):
        parts.append("[green]Package ready[/green]")
    if alerts.get("staged_apply_plan_available"):
        parts.append("[cyan]Staged apply-plan preview[/cyan]")
    if alerts.get("benchmark_regression_detected"):
        parts.append("[red]Benchmark regression[/red]")
    if not parts:
        console.print("[dim]Alerts: none[/dim]")
    else:
        console.print("[dim]Alerts:[/dim] " + "  |  ".join(parts))
    console.print()


def _render_cohort_summary(console: Console, data: dict) -> None:
    """C3: Active cohort summary + recent recommendation (operator-facing)."""
    summary = data.get("cohort_summary") or {}
    cohort_name = summary.get("active_cohort_name") or "—"
    sessions = summary.get("sessions_count", 0)
    avg_u = summary.get("avg_usefulness")
    rec = summary.get("recent_recommendation") or ""
    lines = [
        f"  [bold]Active cohort:[/bold] {cohort_name}",
        f"  [bold]Sessions:[/bold] {sessions}",
        f"  [bold]Avg usefulness:[/bold] {avg_u if avg_u is not None else '—'}",
        f"  [bold]Recent recommendation:[/bold] {rec[:120] + ('…' if len(rec) > 120 else '') if rec else '—'}",
    ]
    console.print(Panel("\n".join(lines), title="Cohort summary", border_style="magenta"))


def _render_dashboard_content(console: Console, data: dict, compact: bool = False) -> None:
    """Render dashboard panels from get_dashboard_data() result. Used by both TUI and CLI."""
    workflow_filter = data.get("workflow_filter")
    if workflow_filter:
        console.print(f"[dim]▸ Filter: workflow = [bold]{workflow_filter}[/bold][/dim]\n")

    _render_alert_strip(console, data)
    _render_cohort_summary(console, data)
    console.print()

    readiness = data.get("readiness") or {}
    ready = readiness.get("ready", False)
    safe = readiness.get("safe_to_demo", False)
    adapter_ok = readiness.get("adapter_ok", False)
    degraded = readiness.get("degraded", False)
    blocking = readiness.get("blocking") or []
    warnings = readiness.get("warnings") or []
    latest_run = readiness.get("latest_run_dir", "")

    console.print("[dim]——— Readiness ———[/dim]")
    console.print(Panel(
        "[bold]Readiness[/bold]\n"
        + ("[green]Ready · Safe to demo[/green]" if ready and safe else "[yellow]Not ready or not safe to demo[/yellow]")
        + ("\n[dim]Degraded: no adapter (base model only)[/dim]" if degraded else "")
        + ("\n[green]Adapter: OK[/green]" if adapter_ok and not degraded else ""),
        title="1. Readiness",
        border_style="green" if ready else "yellow",
    ))
    for b in blocking[:3]:
        console.print(f"  [red]Blocking: {b}[/red]")
    for w in warnings[:3]:
        console.print(f"  [yellow]{w}[/yellow]")
    if latest_run:
        console.print(f"  [dim]Latest run: {latest_run}[/dim]")

    workspaces = data.get("recent_workspaces") or []
    console.print("[dim]——— Workspaces & review ———[/dim]")
    console.print(Panel(
        f"[bold]Recent workspaces[/bold]\n[dim]{len(workspaces)} workspace(s)" + (f" (filtered: {workflow_filter})" if workflow_filter else " under data/local/workspaces/") + "[/dim]",
        title="2. Recent workspaces",
        border_style="blue",
    ))
    if not workspaces:
        console.print("  [dim]None. Run: workflow-dataset release demo --save-artifact[/dim]")
    else:
        for w in workspaces[:7]:
            status = w.get("status", "?")
            chip = "[green]package_ready[/green]" if status == "package_ready" else "[yellow]package_pending[/yellow]" if status == "package_pending" else "[dim]review_pending[/dim]"
            console.print(f"  [bold]{w.get('workflow', '?')}[/bold]  {Path(w.get('workspace_path', '')).name}  {w.get('artifact_count', 0)} artifacts  {chip}")
            if not compact:
                console.print(f"    [dim]{w.get('workspace_path', '')}[/dim]")

    rp = data.get("review_package") or {}
    unreviewed = rp.get("unreviewed_count", 0)
    pkg_pending = rp.get("package_pending_count", 0)
    latest_pkg = rp.get("latest_package_path")
    pkg_count = rp.get("packages_count", 0)
    staging = data.get("staging") or {}
    staged_count = staging.get("staged_count", 0)
    last_preview = staging.get("last_apply_plan_preview_path")
    console.print("[dim]——— Packages & staging ———[/dim]")
    console.print(Panel(
        "[bold]Review / package queue[/bold]\n"
        + f"  Workspaces awaiting review: {unreviewed}\n"
        + f"  Approved but no package yet: {pkg_pending}\n"
        + f"  Packages built: {pkg_count}\n"
        + (f"  [dim]Latest package: {latest_pkg}[/dim]" if latest_pkg else "  [dim]No package built yet.[/dim]")
        + f"\n  [bold]Staging board:[/bold] {staged_count} item(s) staged"
        + (f"\n  [dim]Last apply-plan preview: {last_preview}[/dim]" if last_preview else ""),
        title="3. Review & package & staging",
        border_style="blue",
    ))

    cohort = data.get("cohort") or {}
    reports = cohort.get("cohort_reports") or []
    agg_path = cohort.get("aggregate_path")
    rec = cohort.get("recommendation")
    sessions_count = cohort.get("sessions_count", 0)
    avg_u = cohort.get("avg_usefulness")
    console.print("[dim]——— Cohort state ———[/dim]")
    console.print(Panel(
        "[bold]Cohort / pilot[/bold]\n"
        + f"  Sessions (aggregate): {sessions_count}\n"
        + (f"  Avg usefulness: {avg_u}" if avg_u is not None else "")
        + ("\n  [dim]Recommendation: " + str(rec)[:80] + ("…" if len(str(rec or "")) > 80 else "") + "[/dim]" if rec else "")
        + (f"\n  [dim]Cohort reports: {len(reports)} (e.g. {reports[0]['name']})[/dim]" if reports else "\n  [dim]No cohort reports. Run pilot cohort-report --cohort <id>[/dim]"),
        title="4. Cohort",
        border_style="blue",
    ))
    if agg_path:
        console.print(f"  [dim]Aggregate: {agg_path}[/dim]")

    actions = data.get("next_actions") or []
    console.print("[dim]——— Next actions ———[/dim]")
    console.print(Panel(
        "[bold]Recommended next actions[/bold]\n[dim]Run these commands to proceed (copy-paste ready).[/dim]",
        title="5. Next actions",
        border_style="cyan",
    ))
    if not actions:
        console.print("  [dim]Run release demo --save-artifact to create a workspace.[/dim]")
    else:
        for i, a in enumerate(actions[:6], 1):
            console.print(f"  [cyan]{i}.[/cyan] {a.get('label', '')}")
            console.print(f"     [dim]{a.get('command', '')}[/dim]")

    # Local sources (provenance): exact paths used
    sources = data.get("local_sources") or {}
    if sources:
        lines = [
            f"  [bold]repo_root:[/bold] {sources.get('repo_root', '')}",
            f"  [bold]workspaces:[/bold] {sources.get('workspaces_root', '')}",
            f"  [bold]pilot:[/bold] {sources.get('pilot_dir', '')}",
            f"  [bold]packages:[/bold] {sources.get('packages_root', '')}",
            f"  [bold]review:[/bold] {sources.get('review_root', '')}",
            f"  [bold]staging:[/bold] {sources.get('staging_dir', '')}",
        ]
        if sources.get("pilot_readiness_report"):
            lines.append(f"  [bold]readiness report:[/bold] {sources['pilot_readiness_report']}")
        if sources.get("release_readiness_report"):
            lines.append(f"  [bold]release report:[/bold] {sources['release_readiness_report']}")
        console.print(Panel(
            "\n".join(lines),
            title="6. Local sources (provenance)",
            border_style="dim",
        ))
    else:
        console.print("[dim]Sources: data/local/workspaces/, data/local/pilot/, data/local/review/, data/local/packages/[/dim]")
    # C4: Action shortcuts (operator macros)
    macros = data.get("action_macros") or []
    if macros:
        console.print("[dim]——— Action shortcuts ———[/dim]")
        console.print(Panel(
            "\n".join(
                f"  [cyan]{i}.[/cyan] {m.get('label', '')}\n     [dim]{m.get('command', '')}[/dim]"
                for i, m in enumerate(macros, 1)
            ) or "  [dim]None[/dim]",
            title="Action shortcuts (run via: workflow-dataset dashboard action <id>)",
            border_style="cyan",
        ))
    console.print("[dim]Drill-downs: workflow-dataset dashboard workspace | package | cohort | apply-plan[/dim]")
    console.print()


def render_dashboard(console: Console, state: ConsoleState, settings: Settings) -> Screen:
    """Render Local Reporting Command Center. Supports drill-downs W/P/C/A. Returns next screen (HOME)."""
    try:
        from workflow_dataset.release.dashboard_data import get_dashboard_data, get_dashboard_drilldown
    except ImportError:
        console.print("[red]Dashboard data module not available.[/red]")
        Prompt.ask("Press Enter to return to Home", default="")
        return Screen.HOME

    config_path = getattr(state, "config_path", "configs/settings.yaml")
    from workflow_dataset.path_utils import get_repo_root
    repo_root = Path(get_repo_root())

    while True:
        data = get_dashboard_data(config_path=config_path, repo_root=repo_root)
        console.print(Panel(
            "[bold]Local Reporting Command Center[/bold]\n"
            "[dim]Generate → Inspect → Review → Package → Cohort · All local, sandbox-only[/dim]",
            title="Dashboard",
            border_style="blue",
        ))
        console.print()
        _render_dashboard_content(console, data, compact=False)
        macros = data.get("action_macros") or []
        console.print("[dim]1-5: Run shortcut | W/P/C/A: Drill-down | Enter: Home[/dim]")
        choice = Prompt.ask("Choice", default="").strip().upper()
        if not choice or choice == "ENTER":
            return Screen.HOME
        # C4: Run action macro by index (1-based)
        if choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(macros):
                macro = macros[idx - 1]
                cmd = macro.get("command", "")
                if cmd:
                    console.print(f"[dim]Running: {cmd}[/dim]\n")
                    try:
                        result = subprocess.run(
                            cmd,
                            shell=True,
                            cwd=str(repo_root),
                            capture_output=True,
                            text=True,
                            timeout=60,
                        )
                        if result.stdout:
                            console.print(result.stdout)
                        if result.stderr:
                            console.print(f"[yellow]{result.stderr}[/yellow]")
                        if result.returncode != 0:
                            console.print(f"[dim]Exit code: {result.returncode}[/dim]")
                    except subprocess.TimeoutExpired:
                        console.print("[yellow]Command timed out.[/yellow]")
                    except Exception as e:
                        console.print(f"[red]Error: {e}[/red]")
                    Prompt.ask("Press Enter to return to dashboard", default="")
                    console.print()
                continue
        drill_map = {"W": "workspace", "P": "package", "C": "cohort", "A": "apply_plan"}
        if choice in drill_map:
            drill_data = get_dashboard_drilldown(repo_root=repo_root, drill=drill_map[choice])
            console.print()
            _render_drilldown(console, drill_data)
            Prompt.ask("Press Enter to return to dashboard", default="")
            console.print()
        else:
            console.print("[dim]Enter, 1-5, or W/P/C/A.[/dim]")


def print_dashboard_cli(
    console: Console,
    config_path: str = "configs/settings.yaml",
    workflow_filter: str | None = None,
) -> None:
    """Print dashboard to console (for CLI command workflow-dataset dashboard). No prompt."""
    from workflow_dataset.release.dashboard_data import get_dashboard_data
    from workflow_dataset.path_utils import get_repo_root
    repo_root = Path(get_repo_root())
    data = get_dashboard_data(config_path=config_path, repo_root=repo_root, workflow_filter=workflow_filter)
    subtitle = "workflow-dataset dashboard" + (f" --workflow {workflow_filter}" if workflow_filter else "")
    console.print(Panel(
        f"[bold]Local Reporting Command Center[/bold]\n[dim]{subtitle}[/dim]",
        title="Dashboard",
        border_style="blue",
    ))
    console.print()
    _render_dashboard_content(console, data, compact=True)


def _render_drilldown(console: Console, data: dict) -> None:
    """Render one drill-down (workspace, package, cohort, apply_plan) from get_dashboard_drilldown()."""
    drill_type = data.get("drill_type", "?")
    path = data.get("path")
    ref = data.get("ref")
    payload = data.get("payload") or {}
    if not path and not payload:
        console.print("[dim]No data for this drill-down.[/dim]")
        return
    title = {"workspace": "Latest workspace", "package": "Latest package", "cohort": "Latest cohort report", "apply_plan": "Latest apply-plan preview"}.get(drill_type, drill_type)
    console.print(Panel(
        f"[bold]{title}[/bold]\n[dim]Path: {path or '—'}[/dim]" + (f"\n[dim]Ref: {ref}[/dim]" if ref else ""),
        title=f"Drill-down: {drill_type}",
        border_style="cyan",
    ))
    if drill_type == "workspace":
        console.print(f"  [bold]Workflow:[/bold] {payload.get('workflow', '—')}")
        console.print(f"  [bold]Run ID:[/bold] {payload.get('run_id', '—')}")
        console.print(f"  [bold]Artifacts:[/bold] {payload.get('artifacts', [])}")
        console.print(f"  [bold]Approved:[/bold] {payload.get('approved_artifacts', [])}")
        if payload.get("inspect_command"):
            console.print(f"  [dim]Inspect: {payload['inspect_command']}[/dim]")
        if payload.get("build_package_command"):
            console.print(f"  [dim]Build package: {payload['build_package_command']}[/dim]")
    elif drill_type == "package":
        console.print(f"  [bold]Files:[/bold] {payload.get('files', [])}")
        if payload.get("open_command"):
            console.print(f"  [dim]{payload['open_command']}[/dim]")
    elif drill_type == "cohort":
        if payload.get("excerpt"):
            console.print(f"  [dim]{payload['excerpt'][:500]}{'…' if len(payload.get('excerpt', '')) > 500 else ''}[/dim]")
        if payload.get("open_command"):
            console.print(f"  [dim]{payload['open_command']}[/dim]")
    elif drill_type == "apply_plan":
        if payload.get("excerpt"):
            console.print(f"  [dim]{payload['excerpt'][:600]}{'…' if len(payload.get('excerpt', '')) > 600 else ''}[/dim]")
        if payload.get("open_command"):
            console.print(f"  [dim]{payload['open_command']}[/dim]")
    console.print()


def print_drilldown_cli(
    console: Console,
    drill: str,
    config_path: str = "configs/settings.yaml",
    workflow_filter: str | None = None,
) -> None:
    """Print one drill-down to console (for CLI workflow-dataset dashboard workspace | package | cohort | apply-plan)."""
    from workflow_dataset.release.dashboard_data import get_dashboard_drilldown
    from workflow_dataset.path_utils import get_repo_root
    repo_root = Path(get_repo_root())
    data = get_dashboard_drilldown(repo_root=repo_root, drill=drill, workflow_filter=workflow_filter)
    console.print(Panel(
        f"[bold]Command center drill-down[/bold]\n[dim]workflow-dataset dashboard {drill}[/dim]",
        title="Dashboard",
        border_style="blue",
    ))
    console.print()
    _render_drilldown(console, data)

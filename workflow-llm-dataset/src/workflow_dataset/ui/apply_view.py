"""
Apply view: choose workspace and target, build plan, diff preview, explicit confirm, execute.

Safety: apply requires explicit confirmation; show backup/rollback availability.
"""

from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from workflow_dataset.settings import Settings
from workflow_dataset.ui.models import Screen
from workflow_dataset.ui.state_store import ConsoleState
from workflow_dataset.ui.services import (
    get_workspaces,
    get_workspace_preview,
    build_apply_plan,
    get_diff_preview,
    execute_apply,
)


def render_apply(console: Console, state: ConsoleState, settings: Settings) -> Screen:
    """Apply flow: workspace → target → plan → preview → confirm → execute. Returns next screen."""
    ap = getattr(settings, "apply", None)
    if not ap or not getattr(ap, "apply_enabled", False):
        console.print(Panel(
            "[yellow]Apply is disabled.[/yellow]\nEnable apply.apply_enabled in config to use this flow.",
            title="Apply",
            border_style="yellow",
        ))
        Prompt.ask("\n[dim]Press Enter to return[/dim]", default="")
        return Screen.HOME

    console.print(Panel(
        "[bold]Apply sandbox → target[/bold]\n[dim]Preview only until you confirm. Backups created; rollback available.[/dim]\n[red]Action: APPLY — requires explicit confirmation[/red]",
        title="Apply",
        border_style="blue",
    ))

    selected_paths: list[str] | None = None
    workspace_path = ""
    if state.pending_adoption_candidate:
        cand = state.pending_adoption_candidate
        console.print(Panel(
            f"[bold]Pending adoption[/bold]\nworkspace: {cand.get('workspace_path', '')}\npaths: {cand.get('candidate_paths', [])}",
            title="Generation adoption candidate",
            border_style="cyan",
        ))
    use_pending = state.pending_adoption_candidate and Prompt.ask("Use this adoption candidate? (Y/n)", default="y").strip().lower() != "n"
    if use_pending and state.pending_adoption_candidate:
        workspace_path = state.pending_adoption_candidate.get("workspace_path", "")
        selected_paths = state.pending_adoption_candidate.get("candidate_paths") or None
        state.clear_pending_adoption_candidate()
    if not workspace_path:
        workspaces = get_workspaces(settings, session_id=state.selected_session_id or "", limit=30)
        if not workspaces:
            console.print("[yellow]No workspaces. Materialize a draft/suggestion first.[/yellow]")
            Prompt.ask("\n[dim]Press Enter to return[/dim]", default="")
            return Screen.HOME

        table = Table(title="Workspaces")
        table.add_column("#", style="dim", width=4)
        table.add_column("Name", style="cyan")
        table.add_column("Path", style="dim")
        for i, w in enumerate(workspaces[:20], 1):
            table.add_row(str(i), w.get("name", ""), (w.get("path", ""))[:60])
        console.print(table)

        ws_sel = Prompt.ask("Workspace number (or Enter to skip)", default="").strip()
        if not ws_sel:
            return Screen.HOME
        if not ws_sel.isdigit() or not (1 <= int(ws_sel) <= len(workspaces)):
            console.print("[yellow]Invalid workspace.[/yellow]")
            return Screen.APPLY
        workspace_path = workspaces[int(ws_sel) - 1].get("path", "")
    state.set_workspace(workspace_path)

    target_path = Prompt.ask("Target directory path (absolute or relative)", default="").strip()
    if not target_path:
        console.print("[yellow]No target path.[/yellow]")
        return Screen.APPLY
    target_path = str(Path(target_path).resolve())

    allow_overwrite = Prompt.ask("Allow overwrite of existing files? (y/N)", default="n").strip().lower() == "y"

    # Build plan (preview only)
    plan, err = build_apply_plan(settings, workspace_path, target_path, allow_overwrite=allow_overwrite, selected_paths=selected_paths)
    if err:
        console.print(f"[red]{err}[/red]")
        Prompt.ask("[dim]Press Enter to return[/dim]", default="")
        return Screen.HOME
    if not plan:
        console.print("[yellow]No plan generated.[/yellow]")
        return Screen.APPLY

    console.print(Panel(get_diff_preview(plan), title="[bold]Diff preview (inspect only — not executed)[/bold]", border_style="yellow"))
    console.print("\n[bold]What will happen:[/bold]")
    console.print("  • Files listed above will be copied from sandbox to target.")
    console.print("  • Existing files will be backed up if apply_create_backups is true.")
    console.print("  • You will receive a rollback token to restore if needed.")

    confirm = Prompt.ask("\n[red]Type 'yes' to confirm and execute apply[/red]", default="").strip().lower()
    if confirm != "yes":
        console.print("[dim]Apply cancelled. No files were changed.[/dim]")
        Prompt.ask("[dim]Press Enter to return[/dim]", default="")
        return Screen.HOME

    result, exec_err = execute_apply(settings, workspace_path, target_path, allow_overwrite=allow_overwrite, selected_paths=selected_paths)
    if exec_err:
        console.print(f"[red]{exec_err}[/red]")
    else:
        console.print(f"[green]Applied {len(result.applied_paths)} path(s)[/green] → {target_path}")
        if result.rollback_token:
            console.print(Panel(f"[bold]Rollback token[/bold]: {result.rollback_token}\n[dim]Use Rollback screen to restore if needed.[/dim]", title="Backup / rollback", border_style="green"))

    Prompt.ask("[dim]Press Enter to return to home[/dim]", default="")
    return Screen.HOME

"""
Materialize view: choose draft/suggestion, materialize to sandbox, show preview.

Safety: sandbox only — no real project writes.
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
    get_drafts,
    get_suggestions,
    get_workspaces,
    run_materialize,
    get_workspace_preview,
)


def render_materialize(console: Console, state: ConsoleState, settings: Settings) -> Screen:
    """Choose draft or suggestion, run materialization to sandbox, show preview. Returns next screen."""
    console.print(Panel(
        "[bold]Materialize to sandbox[/bold]\n[dim]Draft or suggestion → workspace only (no real project writes)[/dim]\n[yellow]Action: SANDBOX — inspect only until you choose Apply[/yellow]",
        title="Materialize",
        border_style="blue",
    ))

    mat = getattr(settings, "materialization", None)
    if not getattr(mat, "materialization_enabled", True):
        console.print("[red]Materialization is disabled in config.[/red]")
        Prompt.ask("\n[dim]Press Enter to return[/dim]", default="")
        return Screen.HOME

    drafts = get_drafts(settings)
    suggestions = get_suggestions(settings)

    if not drafts and not suggestions:
        console.print("[yellow]No drafts or suggestions. Run assist suggest and assist draft first.[/yellow]")
        Prompt.ask("\n[dim]Press Enter to return[/dim]", default="")
        return Screen.HOME

    # Choose source: draft or suggestion
    console.print("\n[bold]Source[/bold]")
    if drafts:
        for i, d in enumerate(drafts[:15], 1):
            console.print(f"  [cyan]d{i}[/cyan] {getattr(d, 'draft_type', '')} — {getattr(d, 'title', '')[:40]}")
    if suggestions:
        for i, s in enumerate(suggestions[:15], 1):
            console.print(f"  [cyan]s{i}[/cyan] suggestion — {getattr(s, 'title', '')[:40]} (id: {getattr(s, 'suggestion_id', '')[:20]})")

    src = Prompt.ask("Choose: d<N> draft, s<N> suggestion (or Enter to skip)", default="").strip().lower()
    if not src:
        return Screen.HOME

    draft_type = ""
    suggestion_id = ""
    if src.startswith("d") and src[1:].isdigit() and drafts:
        idx = int(src[1:])
        if 1 <= idx <= len(drafts):
            draft_type = getattr(drafts[idx - 1], "draft_type", "") or "project_brief"
    elif src.startswith("s") and src[1:].isdigit() and suggestions:
        idx = int(src[1:])
        if 1 <= idx <= len(suggestions):
            suggestion_id = getattr(suggestions[idx - 1], "suggestion_id", "") or ""

    if not draft_type and not suggestion_id:
        console.print("[yellow]Invalid choice.[/yellow]")
        return Screen.MATERIALIZE

    use_llm = Prompt.ask("Use LLM for refinement? (y/N)", default="n").strip().lower() == "y"

    try:
        manifest, ws_path = run_materialize(
            settings,
            draft_type=draft_type,
            suggestion_id=suggestion_id,
            session_id=state.selected_session_id or None,
            project_id=state.selected_project_id,
            use_llm=use_llm,
        )
        state.set_workspace(ws_path)
        console.print(f"\n[green]Materialized {len(manifest.output_paths)} output(s)[/green] → [dim]{ws_path}[/dim]")
        preview = get_workspace_preview(ws_path)
        if preview:
            console.print(Panel(preview[:2500] + ("..." if len(preview) > 2500 else ""), title="Workspace preview", border_style="dim"))
    except Exception as e:
        console.print(f"[red]{e}[/red]")

    Prompt.ask("[dim]Press Enter to return to home[/dim]", default="")
    return Screen.HOME

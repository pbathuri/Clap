"""
Setup summary view: sessions, progress, summary markdown.
"""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from workflow_dataset.settings import Settings
from workflow_dataset.ui.models import Screen
from workflow_dataset.ui.state_store import ConsoleState
from workflow_dataset.ui.services import get_setup_sessions, get_setup_progress, get_setup_summary_markdown


def render_setup(console: Console, state: ConsoleState, settings: Settings) -> Screen:
    """Show setup sessions, progress, and summary. Returns next screen."""
    console.print(Panel("[bold]Setup summary[/bold]\n[dim]Sessions and onboarding status[/dim]", title="Setup", border_style="blue"))

    sessions = get_setup_sessions(settings)
    if not sessions:
        console.print("[yellow]No setup sessions yet. Run: workflow-dataset setup init[/yellow]")
        Prompt.ask("\n[dim]Press Enter to return[/dim]", default="")
        return Screen.HOME

    # Session selector if multiple
    sid = state.selected_session_id
    if not sid and sessions:
        sid = sessions[0]["session_id"]
        state.set_session(sid)
    if len(sessions) > 1:
        table = Table(title="Sessions")
        table.add_column("#", style="dim", width=4)
        table.add_column("Session ID", style="cyan")
        for i, s in enumerate(sessions, 1):
            table.add_row(str(i), s["session_id"])
        console.print(table)
        sel = Prompt.ask("Session number (or Enter for current)", default="")
        if sel.isdigit() and 1 <= int(sel) <= len(sessions):
            sid = sessions[int(sel) - 1]["session_id"]
            state.set_session(sid)

    progress = get_setup_progress(settings, sid)
    if progress:
        t = Table(show_header=False)
        t.add_column("Field", style="cyan")
        t.add_column("Value", style="green")
        t.add_row("Session", progress.get("session_id", ""))
        t.add_row("Stage", progress.get("current_stage", ""))
        t.add_row("Files scanned", str(progress.get("files_scanned", 0)))
        t.add_row("Artifacts classified", str(progress.get("artifacts_classified", 0)))
        t.add_row("Docs parsed", str(progress.get("docs_parsed", 0)))
        t.add_row("Projects detected", str(progress.get("projects_detected", 0)))
        t.add_row("Style patterns", str(progress.get("style_patterns_extracted", 0)))
        t.add_row("Graph nodes", str(progress.get("graph_nodes_created", 0)))
        console.print(t)

    summary_md = get_setup_summary_markdown(settings, sid)
    if summary_md:
        console.print(Panel(summary_md[:3000] + ("..." if len(summary_md) > 3000 else ""), title="Summary report", border_style="dim"))
    else:
        console.print("[dim]No summary report yet. Complete setup run to generate.[/dim]")

    console.print()
    Prompt.ask("[dim]Press Enter to return to home[/dim]", default="")
    return Screen.HOME

"""
Project explorer: list projects, domain/style, related drafts and suggestions.
"""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from workflow_dataset.settings import Settings
from workflow_dataset.ui.models import Screen, evidence_snippet
from workflow_dataset.ui.state_store import ConsoleState
from workflow_dataset.ui.services import get_projects, get_assistive_context


def render_project(console: Console, state: ConsoleState, settings: Settings) -> Screen:
    """List projects and show context (domain, style, artifacts). Returns next screen."""
    console.print(Panel("[bold]Project explorer[/bold]\n[dim]Detected projects, domains, style profiles[/dim]", title="Projects", border_style="blue"))

    projects = get_projects(settings)
    if not projects:
        console.print("[yellow]No projects in graph. Run setup and graph enrichment first.[/yellow]")
        Prompt.ask("\n[dim]Press Enter to return[/dim]", default="")
        return Screen.HOME

    table = Table(title="Projects")
    table.add_column("#", style="dim", width=4)
    table.add_column("Label", style="cyan")
    table.add_column("Node ID", style="dim")
    for i, p in enumerate(projects[:30], 1):
        label = p.get("label", p.get("node_id", ""))[:40]
        nid = (p.get("node_id") or "")[:24]
        table.add_row(str(i), label, nid)
    console.print(table)

    context = get_assistive_context(settings, state.selected_session_id or None)
    domains = context.get("domains") or []
    if domains:
        console.print("\n[bold]Domains[/bold]")
        for d in domains[:10]:
            console.print(f"  • {d.get('label', d.get('node_id', ''))}")

    style_signals = context.get("style_signals") or []
    if style_signals:
        console.print("\n[bold]Style signals (evidence)[/bold]")
        console.print(f"  {evidence_snippet([s.get('pattern_type') or s.get('description', '') for s in style_signals], 5)}")

    parsed = context.get("parsed_artifacts") or []
    if parsed:
        console.print(f"\n[dim]Parsed artifacts: {len(parsed)} (session: {state.selected_session_id or 'latest'})[/dim]")

    sel = Prompt.ask("\nProject number to select for context (or Enter to skip)", default="")
    if sel.isdigit() and 1 <= int(sel) <= len(projects):
        state.set_project(projects[int(sel) - 1].get("node_id", ""))

    Prompt.ask("[dim]Press Enter to return to home[/dim]", default="")
    return Screen.HOME

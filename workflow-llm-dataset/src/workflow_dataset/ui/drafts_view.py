"""
Drafts view: list and inspect draft structures with style signals.
"""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from workflow_dataset.settings import Settings
from workflow_dataset.ui.models import Screen, evidence_snippet
from workflow_dataset.ui.state_store import ConsoleState
from workflow_dataset.ui.services import get_drafts


def render_drafts(console: Console, state: ConsoleState, settings: Settings) -> Screen:
    """List draft structures and show sections/evidence. Returns next screen."""
    console.print(Panel("[bold]Draft structures[/bold]\n[dim]Generated outlines and scaffolds[/dim]", title="Drafts", border_style="blue"))

    drafts = get_drafts(settings)
    if not drafts:
        console.print("[yellow]No draft structures yet. Run: workflow-dataset assist draft[/yellow]")
        Prompt.ask("\n[dim]Press Enter to return[/dim]", default="")
        return Screen.HOME

    table = Table(title="Draft structures")
    table.add_column("#", style="dim", width=4)
    table.add_column("Type", style="cyan", width=28)
    table.add_column("Title", style="green")
    table.add_column("Sections", style="dim")
    for i, d in enumerate(drafts[:25], 1):
        dtype = getattr(d, "draft_type", "") or ""
        title = (getattr(d, "title", None) or "")[:40]
        sections = getattr(d, "recommended_sections", None) or []
        table.add_row(str(i), dtype, title, evidence_snippet(sections, 4))
    console.print(table)

    console.print("\n[bold]Style signals supporting draft structure[/bold]")
    for i, d in enumerate(drafts[:5], 1):
        dtype = getattr(d, "draft_type", "")
        outline = (getattr(d, "structure_outline", "") or "")[:200]
        console.print(f"  [cyan]{i}. {dtype}[/cyan]")
        if outline:
            console.print(f"     [dim]{outline}{'…' if len(outline) >= 200 else ''}[/dim]")

    sel = Prompt.ask("\nDraft number to use for materialize (or Enter to skip)", default="")
    if sel.isdigit() and 1 <= int(sel) <= len(drafts):
        d = drafts[int(sel) - 1]
        state.selected_draft_type = getattr(d, "draft_type", "") or ""

    Prompt.ask("[dim]Press Enter to return to home[/dim]", default="")
    return Screen.HOME

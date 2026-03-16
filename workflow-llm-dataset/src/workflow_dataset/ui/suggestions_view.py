"""
Suggestions view: list and inspect style-aware suggestions with rationale/evidence.
"""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from workflow_dataset.settings import Settings
from workflow_dataset.ui.models import Screen, evidence_snippet
from workflow_dataset.ui.state_store import ConsoleState
from workflow_dataset.ui.services import get_suggestions


def render_suggestions(console: Console, state: ConsoleState, settings: Settings) -> Screen:
    """List suggestions and show rationale/evidence. Returns next screen."""
    console.print(Panel("[bold]Suggestions[/bold]\n[dim]Style-aware suggestions with rationale and evidence[/dim]", title="Suggestions", border_style="blue"))

    suggestions = get_suggestions(settings)
    if not suggestions:
        console.print("[yellow]No suggestions yet. Run: workflow-dataset assist suggest[/yellow]")
        Prompt.ask("\n[dim]Press Enter to return[/dim]", default="")
        return Screen.HOME

    table = Table(title="Suggestions")
    table.add_column("#", style="dim", width=4)
    table.add_column("Type", style="cyan", width=14)
    table.add_column("Title", style="green")
    table.add_column("Confidence", justify="right", width=8)
    for i, s in enumerate(suggestions[:25], 1):
        title = (getattr(s, "title", None) or str(s))[:50]
        stype = getattr(s, "suggestion_type", "") or ""
        conf = getattr(s, "confidence_score", 0)
        table.add_row(str(i), stype, title, f"{conf:.2f}")
    console.print(table)

    console.print("\n[bold]Evidence-aware: why this suggestion exists[/bold]")
    for i, s in enumerate(suggestions[:5], 1):
        rationale = getattr(s, "rationale", "") or ""
        signals = getattr(s, "supporting_signals", None) or []
        sug_id = getattr(s, "suggestion_id", "")
        console.print(f"  [cyan]{i}. {getattr(s, 'title', '')[:40]}[/cyan]")
        console.print(f"     [dim]Rationale: {rationale[:120]}{'…' if len(rationale) > 120 else ''}[/dim]")
        if signals:
            console.print(f"     [dim]Signals: {evidence_snippet(signals, 3)}[/dim]")
        if sug_id:
            console.print(f"     [dim]ID: {sug_id}[/dim]")

    sel = Prompt.ask("\nSuggestion number to use later for materialize (or Enter to skip)", default="")
    if sel.isdigit() and 1 <= int(sel) <= len(suggestions):
        s = suggestions[int(sel) - 1]
        state.selected_suggestion_id = getattr(s, "suggestion_id", "") or ""

    Prompt.ask("[dim]Press Enter to return to home[/dim]", default="")
    return Screen.HOME

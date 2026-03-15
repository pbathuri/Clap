"""
Home screen: system summary, setup/session status, counts.
"""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from workflow_dataset.settings import Settings
from workflow_dataset.ui.models import Screen
from workflow_dataset.ui.state_store import ConsoleState
from workflow_dataset.ui.services import get_home_counts, get_llm_status


def render_home(console: Console, state: ConsoleState, settings: Settings) -> Screen:
    """Show home summary and main menu. Returns next screen."""
    counts = get_home_counts(settings, state.selected_session_id or None)

    console.print(Panel("[bold]Local Operator Console[/bold]\n[dim]Setup · Projects · Suggestions · Drafts · Materialize · Apply · Rollback · Chat[/dim]", title="Home", border_style="blue"))

    table = Table(show_header=False)
    table.add_column("Metric", style="cyan")
    table.add_column("Count", justify="right", style="green")
    table.add_row("Setup sessions", str(counts["sessions"]))
    table.add_row("Projects", str(counts["projects"]))
    table.add_row("Domains", str(counts["domains"]))
    table.add_row("Style profiles", str(counts["style_profiles"]))
    table.add_row("Suggestions", str(counts["suggestions"]))
    table.add_row("Draft structures", str(counts["drafts"]))
    table.add_row("Workspaces", str(counts["workspaces"]))
    table.add_row("Rollback records", str(counts["rollback_records"]))
    table.add_row("Generations", str(counts.get("generations", 0)))
    llm = get_llm_status()
    llm_label = []
    if llm.get("smoke_available"):
        llm_label.append("smoke")
    if llm.get("full_available"):
        llm_label.append("full")
    table.add_row("LLM adapter", ", ".join(llm_label) if llm_label else "—")
    console.print(table)

    if state.selected_session_id:
        console.print(f"[dim]Current session: {state.selected_session_id}[/dim]")

    console.print()
    console.print("[bold]Menu[/bold]")
    console.print("  [cyan]1[/cyan] Setup summary")
    console.print("  [cyan]2[/cyan] Projects")
    console.print("  [cyan]3[/cyan] Suggestions")
    console.print("  [cyan]4[/cyan] Drafts")
    console.print("  [cyan]5[/cyan] Materialize (draft/suggestion → sandbox)")
    console.print("  [cyan]6[/cyan] Apply (sandbox → target, with confirm)")
    console.print("  [cyan]7[/cyan] Rollback")
    console.print("  [cyan]8[/cyan] Chat / explain")
    console.print("  [cyan]9[/cyan] Generation (style pack, prompt pack, asset plan)")
    console.print("  [cyan]L[/cyan] LLM status (runs, comparison report, demo-suite hint)")
    console.print("  [cyan]q[/cyan] Quit")

    choice = Prompt.ask("Choice", default="1").strip().lower()

    if choice == "q":
        return Screen.EXIT
    if choice == "1":
        return Screen.SETUP
    if choice == "2":
        return Screen.PROJECT
    if choice == "3":
        return Screen.SUGGESTIONS
    if choice == "4":
        return Screen.DRAFTS
    if choice == "5":
        return Screen.MATERIALIZE
    if choice == "6":
        return Screen.APPLY
    if choice == "7":
        return Screen.ROLLBACK
    if choice == "8":
        return Screen.CHAT
    if choice == "9":
        return Screen.GENERATION
    if choice == "l":
        return Screen.LLM_STATUS
    return Screen.HOME

"""
M18: Release mode view — narrow release scope, verify hint, demo/report commands.
"""

from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from workflow_dataset.settings import Settings
from workflow_dataset.ui.models import Screen
from workflow_dataset.ui.state_store import ConsoleState


def render_release(console: Console, state: ConsoleState, settings: Settings) -> Screen:
    """Show first narrow release scope and next steps. No overbuild."""
    console.print(Panel(
        "[bold]First narrow release[/bold]\n"
        "[green]Operations reporting assistant[/green]\n\n"
        "Scope: Summarize reporting workflow, scaffold status, next steps.\n"
        "Local-first · Sandbox-only · Apply with confirm.",
        title="Release",
        border_style="blue",
    ))
    report_dir = Path("data/local/release")
    report_path = report_dir / "release_readiness_report.md"
    if report_path.exists():
        console.print(f"[dim]Report: {report_path}[/dim]")
    else:
        console.print("[dim]Run 'workflow-dataset release report' to generate report.[/dim]")
    console.print()
    console.print("[bold]CLI commands[/bold]")
    console.print("  [cyan]workflow-dataset release verify[/cyan]   — Check setup, graph, adapter, trials")
    console.print("  [cyan]workflow-dataset release run[/cyan]        — Run ops trials (adapter mode)")
    console.print("  [cyan]workflow-dataset release demo[/cyan]       — Founder demo (3 prompts)")
    console.print("  [cyan]workflow-dataset release report[/cyan]    — Write release_readiness_report.md")
    console.print()
    console.print("[dim]See docs/FOUNDER_DEMO_FLOW.md and docs/NOT_YET_SUPPORTED.md.[/dim]")
    console.print()
    Prompt.ask("Press Enter to return to Home", default="")
    return Screen.HOME

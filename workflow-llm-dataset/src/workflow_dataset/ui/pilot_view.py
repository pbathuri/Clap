"""
M20: Pilot mode — status, ready/degraded, latest adapter, feedback report.
"""

from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from workflow_dataset.settings import Settings
from workflow_dataset.ui.models import Screen
from workflow_dataset.ui.state_store import ConsoleState


def render_pilot(console: Console, state: ConsoleState, settings: Settings) -> Screen:
    """Show pilot status: ready, degraded, safe-to-demo, latest adapter, report path."""
    try:
        from workflow_dataset.pilot.health import pilot_status_dict
    except ImportError:
        console.print("[red]Pilot module not available.[/red]")
        Prompt.ask("Press Enter to return to Home", default="")
        return Screen.HOME

    config_path = getattr(state, "config_path", "configs/settings.yaml")
    status = pilot_status_dict(config_path=config_path)

    ready = status.get("ready", False)
    degraded = status.get("degraded", False)
    safe = status.get("safe_to_demo", False)
    adapter_ok = status.get("adapter_ok", False)
    latest_run = status.get("latest_run_dir", "")
    feedback_report = status.get("latest_feedback_report", "")

    console.print(Panel(
        "[bold]Narrow private pilot[/bold]\n"
        "Status · Ready · Degraded · Safe to demo",
        title="Pilot",
        border_style="blue",
    ))
    console.print(f"  [bold]Ready:[/bold] {'Yes' if ready else 'No'}")
    console.print(f"  [bold]Safe to demo:[/bold] {'Yes' if safe else 'No'}")
    if degraded:
        console.print("  [yellow]Degraded: no adapter (using base model)[/yellow]")
    else:
        console.print("  [green]Adapter: OK[/green]")
    if adapter_ok and latest_run:
        console.print(f"  [dim]Latest run: {latest_run}[/dim]")
    for b in status.get("blocking", []):
        console.print(f"  [red]Blocking: {b}[/red]")
    for w in status.get("warnings", []):
        console.print(f"  [yellow]{w}[/yellow]")
    if feedback_report:
        console.print(f"  [dim]Feedback report: {feedback_report}[/dim]")
    console.print()
    console.print("[bold]CLI[/bold]")
    console.print("  [cyan]workflow-dataset pilot verify[/cyan]   — Check readiness (exit 1 if blocking)")
    console.print("  [cyan]workflow-dataset pilot status[/cyan]   — Status summary")
    console.print("  [cyan]workflow-dataset pilot latest-report[/cyan] — Generate pilot_readiness_report.md")
    console.print()
    Prompt.ask("Press Enter to return to Home", default="")
    return Screen.HOME

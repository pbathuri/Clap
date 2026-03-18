"""
M17: Workflow trials view — list scenarios, show report path, hint to run from CLI.
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
from workflow_dataset.ui.services import get_trials_status
from workflow_dataset.trials.trial_registry import list_trials
from workflow_dataset.trials.trial_scenarios import register_all_trials


def render_trials(console: Console, state: ConsoleState, settings: Settings) -> Screen:
    """Show workflow trials status, list scenarios, suggest CLI commands."""
    if not list_trials():
        register_all_trials()
    status = get_trials_status()
    trials = list_trials()

    console.print(Panel(
        "[bold]Workflow trials (M17)[/bold]\n"
        "Run real workflow scenarios across baseline / adapter / retrieval modes.",
        title="Trials",
        border_style="blue",
    ))
    table = Table(show_header=True, header_style="cyan")
    table.add_column("Domain", style="green")
    table.add_column("Count", justify="right")
    table.add_column("Example trial_id", style="dim")
    by_domain: dict[str, list] = {}
    for t in trials:
        by_domain.setdefault(t.domain or "other", []).append(t)
    for domain, group in sorted(by_domain.items()):
        example = group[0].trial_id if group else ""
        table.add_row(domain, str(len(group)), example)
    console.print(table)
    console.print(f"Result count: {status.get('result_count', 0)}")
    if status.get("report_path"):
        console.print(f"Report: {status['report_path']}")
    console.print()
    console.print("[dim]Run from CLI:[/dim]")
    console.print("  workflow-dataset trials list")
    console.print("  workflow-dataset trials run ops_summarize_reporting --mode adapter")
    console.print("  workflow-dataset trials run-suite --modes baseline,adapter")
    console.print("  workflow-dataset trials report")
    console.print()
    choice = Prompt.ask("Press Enter to return to Home", default="")
    return Screen.HOME

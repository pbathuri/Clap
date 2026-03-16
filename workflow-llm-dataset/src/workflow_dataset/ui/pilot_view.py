"""
M20/M21: Pilot mode — status, ready/degraded, latest adapter, session summary, aggregate findings.
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
    """Show pilot status: ready, degraded, safe-to-demo, latest session, aggregate, next action."""
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
        console.print(
            "  [yellow]Degraded mode: no adapter — runs use base model. Train adapter for better outputs.[/yellow]")
    elif adapter_ok:
        console.print("  [green]Adapter: OK[/green]")
    else:
        console.print(
            "  [dim]Adapter: LLM config missing or no adapter.[/dim]")
    if adapter_ok and latest_run:
        console.print(f"  [dim]Latest run: {latest_run}[/dim]")
    for b in status.get("blocking", []):
        console.print(f"  [red]Blocking: {b}[/red]")
    for w in status.get("warnings", []):
        console.print(f"  [yellow]Warning: {w}[/yellow]")
    if feedback_report:
        console.print(f"  [dim]Feedback report: {feedback_report}[/dim]")

    try:
        from workflow_dataset.pilot.session_log import get_latest_session, get_current_session_id
        from workflow_dataset.pilot.aggregate import aggregate_sessions
        current_sid = get_current_session_id()
        latest = get_latest_session()
        if latest:
            console.print()
            console.print("[bold]Latest session[/bold]")
            console.print(f"  {latest.session_id}  " + ("(active)" if current_sid ==
                          latest.session_id else f"ended: {latest.timestamp_end or '—'}"))
            if latest.degraded_mode:
                console.print(
                    "  [yellow]Session was in degraded mode.[/yellow]")
            if latest.disposition:
                console.print(f"  Disposition: {latest.disposition}")
        agg = aggregate_sessions(session_limit=20)
        if agg.get("sessions_count", 0) > 0:
            console.print()
            console.print("[bold]Aggregate (recent sessions)[/bold]")
            console.print(
                f"  Sessions: {agg['sessions_count']}  Degraded: {agg.get('degraded_count', 0)}")
            if agg.get("recurring_blockers"):
                console.print("  Recurring blockers: " +
                              ", ".join(agg["recurring_blockers"][:3]))
            if agg.get("recommendation_summary"):
                console.print("  Recommendation: " + (agg["recommendation_summary"][0][:60] + "…" if len(
                    agg["recommendation_summary"][0]) > 60 else agg["recommendation_summary"][0]))
    except Exception:
        pass

    console.print()
    console.print("[bold]CLI[/bold]")
    console.print(
        "  [cyan]pilot verify[/cyan]         — Check readiness (exit 1 if blocking)")
    console.print("  [cyan]pilot start-session[/cyan] — Start a pilot session")
    console.print(
        "  [cyan]pilot end-session[/cyan]    — End session with notes/disposition")
    console.print(
        "  [cyan]pilot capture-feedback[/cyan] — Record structured feedback")
    console.print(
        "  [cyan]pilot aggregate[/cyan]      — Generate aggregate report")
    console.print(
        "  [cyan]pilot latest-summary[/cyan] — Print latest session summary")
    console.print(
        "  [cyan]pilot latest-report[/cyan]  — Generate pilot_readiness_report.md")
    console.print()
    Prompt.ask("Press Enter to return to Home", default="")
    return Screen.HOME

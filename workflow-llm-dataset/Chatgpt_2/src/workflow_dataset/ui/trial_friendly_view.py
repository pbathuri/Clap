"""
M19: Friendly trial mode — session id, trial tasks, quick feedback, session summary.
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


def render_trial_friendly(console: Console, state: ConsoleState, settings: Settings) -> Screen:
    """Friendly trial: show session, tasks, record feedback, show summary."""
    store_path = Path("data/local/trials")
    try:
        from workflow_dataset.feedback.session_store import get_current_session
        from workflow_dataset.feedback.friendly_tasks import load_friendly_trial_tasks
        from workflow_dataset.feedback.feedback_store import load_feedback_entries, save_feedback_entry, save_session_summary
        from workflow_dataset.feedback.feedback_models import TrialFeedbackEntry, TrialSessionSummary
        from datetime import datetime, timezone
    except ImportError:
        console.print("[red]Feedback module not available.[/red]")
        Prompt.ask("Press Enter to return to Home", default="")
        return Screen.HOME

    sess = get_current_session(store_path)
    session_id = sess.get("session_id", "") or "(none — run: workflow-dataset trial start)"
    user_alias = sess.get("user_alias", "") or "(optional alias)"

    console.print(Panel(
        "[bold]Friendly user trial[/bold]\n"
        "Session · Tasks · Record feedback · Summary",
        title="Trial",
        border_style="green",
    ))
    console.print(f"[bold]Session ID:[/bold] {session_id}")
    console.print(f"[dim]User alias: {user_alias}[/dim]")
    console.print()

    tasks_path = store_path / "friendly_trial_tasks.json"
    tasks = load_friendly_trial_tasks(tasks_path)
    if tasks:
        table = Table(show_header=True, header_style="bold")
        table.add_column("Task ID", style="cyan")
        table.add_column("Priority", style="dim")
        table.add_column("Description")
        for t in tasks[:12]:
            table.add_row(
                t.get("task_id", ""),
                t.get("priority", ""),
                (t.get("short_description", "") or "")[:50] + ("..." if len(t.get("short_description", "") or "") > 50 else ""),
            )
        console.print(table)
    else:
        console.print("[dim]No tasks file: data/local/trials/friendly_trial_tasks.json[/dim]")
    console.print()
    console.print("[bold]Actions[/bold]")
    console.print("  [cyan]1[/cyan] Record quick feedback (task_id, outcome, notes)")
    console.print("  [cyan]2[/cyan] Show session summary")
    console.print("  [cyan]h[/cyan] Back to Home")
    choice = Prompt.ask("Choice", default="h").strip().lower()

    if choice == "1":
        task_id = Prompt.ask("Task ID", default="ops_summarize_reporting").strip()
        outcome = Prompt.ask("Outcome (completed|partial|failed)", default="partial").strip() or "partial"
        usefulness = Prompt.ask("Usefulness 1-5 (0 to skip)", default="0").strip()
        trust = Prompt.ask("Trust 1-5 (0 to skip)", default="0").strip()
        freeform = Prompt.ask("Freeform feedback (optional)", default="").strip()
        try:
            entry = TrialFeedbackEntry(
                user_id_or_alias=user_alias if user_alias != "(optional alias)" else "",
                session_id=sess.get("session_id", ""),
                task_id=task_id,
                workflow_type=task_id.split("_")[0] if "_" in task_id else "",
                outcome_rating=outcome,
                usefulness_rating=int(usefulness) if usefulness.isdigit() else 0,
                trust_rating=int(trust) if trust.isdigit() else 0,
                style_match_rating=0,
                confusion_points="",
                failure_points="",
                freeform_feedback=freeform,
                created_utc=datetime.now(timezone.utc).isoformat(),
            )
            save_feedback_entry(entry, store_path)
            console.print("[green]Feedback saved.[/green]")
        except Exception as e:
            console.print(f"[red]{e}[/red]")
        Prompt.ask("Press Enter to continue", default="")
        return Screen.TRIAL_FRIENDLY

    if choice == "2":
        if not sess.get("session_id"):
            console.print("[yellow]No active session. Run 'workflow-dataset trial start' first.[/yellow]")
        else:
            entries = [e for e in load_feedback_entries(store_path) if e.session_id == sess.get("session_id")]
            completed = sum(1 for e in entries if (e.outcome_rating or "").lower() == "completed")
            summary = TrialSessionSummary(
                user_id_or_alias=sess.get("user_alias", ""),
                session_id=sess["session_id"],
                tasks_attempted=len(entries),
                tasks_completed=completed,
                top_praise_points="",
                top_failure_points="",
                top_requested_features="",
                created_utc=datetime.now(timezone.utc).isoformat(),
            )
            save_session_summary(summary, store_path)
            console.print(f"[green]Session summary: tasks_attempted={summary.tasks_attempted}  tasks_completed={summary.tasks_completed}[/green]")
        Prompt.ask("Press Enter to continue", default="")
        return Screen.TRIAL_FRIENDLY

    return Screen.HOME

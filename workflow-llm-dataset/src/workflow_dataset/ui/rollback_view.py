"""
Rollback view: list rollback records, inspect, explicit confirm, execute rollback.

Safety: rollback requires explicit confirmation.
"""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from workflow_dataset.settings import Settings
from workflow_dataset.ui.models import Screen
from workflow_dataset.ui.state_store import ConsoleState
from workflow_dataset.ui.services import list_rollback_records, get_rollback_record, run_rollback


def render_rollback(console: Console, state: ConsoleState, settings: Settings) -> Screen:
    """List rollback records, show what will be restored, confirm, execute. Returns next screen."""
    ap = getattr(settings, "apply", None)
    if not getattr(ap, "apply_rollback_enabled", True):
        console.print("[red]Rollback is disabled in config.[/red]")
        Prompt.ask("\n[dim]Press Enter to return[/dim]", default="")
        return Screen.HOME

    console.print(Panel(
        "[bold]Rollback[/bold]\n[dim]Restore files from backup using a rollback token.[/dim]\n[red]Action: ROLLBACK — requires explicit confirmation[/red]",
        title="Rollback",
        border_style="blue",
    ))

    records = list_rollback_records(settings)
    if not records:
        console.print("[dim]No rollback records. Apply creates backups and records when you apply.[/dim]")
        Prompt.ask("\n[dim]Press Enter to return[/dim]", default="")
        return Screen.HOME

    table = Table(title="Rollback records")
    table.add_column("#", style="dim", width=4)
    table.add_column("Token", style="cyan")
    table.add_column("Apply ID", style="dim")
    table.add_column("Created", style="dim")
    table.add_column("Affected paths", justify="right")
    for i, r in enumerate(records[:20], 1):
        paths = r.get("affected_paths") or []
        table.add_row(str(i), (r.get("rollback_token") or "")[:24], (r.get("apply_id") or "")[:16], (r.get("created_utc") or "")[:19], str(len(paths)))
    console.print(table)

    console.print("\n[bold]Evidence: what rollback will restore[/bold]")
    console.print("  Each record stores backup paths; rollback copies backups back to original paths.")

    sel = Prompt.ask("Record number to rollback (or Enter to skip)", default="").strip()
    if not sel:
        return Screen.HOME
    if not sel.isdigit() or not (1 <= int(sel) <= len(records)):
        console.print("[yellow]Invalid selection.[/yellow]")
        return Screen.ROLLBACK

    rec = records[int(sel) - 1]
    token = rec.get("rollback_token", "")
    detail = get_rollback_record(settings, token)
    if detail:
        affected = getattr(detail, "affected_paths", None) or []
        console.print(Panel("\n".join(f"  • {p}" for p in affected[:15]) + ("\n  …" if len(affected) > 15 else ""), title="Affected paths (will be restored)", border_style="yellow"))

    confirm = Prompt.ask(f"\n[red]Type 'yes' to confirm rollback for token {token[:20]}…[/red]", default="").strip().lower()
    if confirm != "yes":
        console.print("[dim]Rollback cancelled.[/dim]")
        Prompt.ask("[dim]Press Enter to return[/dim]", default="")
        return Screen.HOME

    ok, msg = run_rollback(settings, token)
    if ok:
        console.print(f"[green]{msg}[/green]")
    else:
        console.print(f"[red]{msg}[/red]")

    Prompt.ask("[dim]Press Enter to return to home[/dim]", default="")
    return Screen.HOME

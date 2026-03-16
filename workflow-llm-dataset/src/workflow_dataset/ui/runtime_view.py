"""
M22: Runtime / packs view: installed packs, active capabilities, resolution summary.
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


def _packs_dir(settings: Settings) -> str:
    """Resolve packs dir from config or default."""
    # Optional: read from settings if we add packs_dir to config
    return "data/local/packs"


def render_runtime(console: Console, state: ConsoleState, settings: Settings) -> Screen:
    """Show installed packs and active capability resolution. Returns next screen."""
    packs_dir = _packs_dir(settings)
    console.print(Panel("[bold]Runtime & capability packs[/bold]\n[dim]Installed packs · Active capabilities[/dim]", title="Runtime", border_style="blue"))

    try:
        from workflow_dataset.packs import list_installed_packs, resolve_active_capabilities
        from workflow_dataset.packs.pack_activation import get_primary_pack_id, get_pinned, get_suspended_pack_ids, get_current_context
        from workflow_dataset.packs.pack_state import get_active_role
        installed = list_installed_packs(packs_dir)
        primary = get_primary_pack_id(packs_dir)
        pinned = get_pinned(packs_dir)
        suspended = get_suspended_pack_ids(packs_dir)
        ctx = get_current_context(packs_dir)
        role = ctx.get("current_role") or get_active_role(packs_dir)
        cap = resolve_active_capabilities(role=role or None, workflow_type=ctx.get("current_workflow") or None, task_type=ctx.get("current_task") or None, packs_dir=packs_dir)
    except Exception as e:
        console.print(f"[red]Error loading runtime: {e}[/red]")
        console.print("[dim]Use CLI: workflow-dataset packs list / runtime status[/dim]")
        Prompt.ask("Press Enter to return")
        return Screen.HOME

    table = Table(show_header=False)
    table.add_column("Item", style="cyan")
    table.add_column("Value", style="green")
    table.add_row("Installed packs", str(len(installed)))
    if installed:
        table.add_row("  IDs", ", ".join(r.get("pack_id", "") for r in installed))
    table.add_row("Primary pack", primary or "—")
    if pinned:
        table.add_row("Pinned", str(pinned))
    if suspended:
        table.add_row("Suspended", ", ".join(suspended))
    if role:
        table.add_row("Current role", role)
    table.add_row("Active capabilities", str(len(cap.active_packs)) + " pack(s)")
    table.add_row("Templates", ", ".join(cap.templates[:5]) + (" …" if len(cap.templates) > 5 else "") if cap.templates else "—")
    table.add_row("Output adapters", ", ".join(cap.output_adapters) if cap.output_adapters else "—")
    console.print(table)

    console.print()
    console.print("[dim]Switch role: workflow-dataset runtime switch-role <role>[/dim]")
    console.print("[dim]Conflicts: workflow-dataset packs conflicts[/dim]")
    console.print("[dim]Explain: workflow-dataset packs explain[/dim]")
    console.print()
    Prompt.ask("Press Enter to return to Home")
    return Screen.HOME

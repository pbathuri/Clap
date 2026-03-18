"""
M29I–M29L: CLI for timeline, inbox, review studio.
"""

from __future__ import annotations

from pathlib import Path

from workflow_dataset.review_studio.timeline import build_timeline
from workflow_dataset.review_studio.inbox import build_inbox
from workflow_dataset.review_studio.studio import get_item, inspect_item, accept_item, reject_item, defer_item


def _root(repo_root: str):
    return Path(repo_root).resolve() if repo_root else None


def cmd_timeline_latest(limit: int = 40, since: str = "", repo_root: str = "") -> None:
    from rich.console import Console
    from rich.table import Table
    console = Console()
    root = _root(repo_root)
    events = build_timeline(repo_root=root, limit=limit, since_iso=since)
    console.print("[bold]Activity timeline[/bold] (newest first)")
    if not events:
        console.print("  [dim]No activity in range.[/dim]")
        return
    t = Table("time", "kind", "summary")
    for e in events[:limit]:
        t.add_row((e.timestamp_utc or "")[:16], e.kind, (e.summary or "")[:60])
    console.print(t)
    console.print("[dim]Filter: workflow-dataset timeline project --id <project_id>[/dim]")


def cmd_timeline_project(project_id: str, limit: int = 30, repo_root: str = "") -> None:
    from rich.console import Console
    from rich.table import Table
    console = Console()
    root = _root(repo_root)
    events = build_timeline(repo_root=root, project_id=project_id, limit=limit)
    console.print(f"[bold]Timeline[/bold] project={project_id}")
    if not events:
        console.print("  [dim]No activity for this project.[/dim]")
        return
    t = Table("time", "kind", "summary")
    for e in events:
        t.add_row((e.timestamp_utc or "")[:16], e.kind, (e.summary or "")[:60])
    console.print(t)


def cmd_inbox_list(status: str = "pending", limit: int = 50, repo_root: str = "") -> None:
    from rich.console import Console
    from rich.table import Table
    console = Console()
    root = _root(repo_root)
    items = build_inbox(repo_root=root, status=status, limit=limit)
    console.print("[bold]Intervention inbox[/bold] " + (f"status={status}" if status else "all"))
    if not items:
        console.print("  [dim]No items.[/dim]")
        console.print("  [dim]workflow-dataset inbox review --id <item_id>  |  inbox accept --id <id>[/dim]")
        return
    t = Table("item_id", "kind", "priority", "summary")
    for i in items:
        t.add_row(i.item_id[:20] + "…" if len(i.item_id) > 20 else i.item_id, i.kind, i.priority, (i.summary or "")[:50])
    console.print(t)
    console.print("[dim]Review: workflow-dataset inbox review --id <item_id>[/dim]")


def cmd_inbox_review(item_id: str, repo_root: str = "") -> None:
    from rich.console import Console
    console = Console()
    root = _root(repo_root)
    info = inspect_item(item_id, root)
    if info.get("error"):
        console.print(f"[red]{info['error']}[/red]")
        return
    console.print("[bold]Inbox item[/bold]")
    console.print(f"  item_id: {info.get('item_id')}")
    console.print(f"  kind: {info.get('kind')}  status: {info.get('status')}  priority: {info.get('priority')}")
    console.print(f"  summary: {info.get('summary')}")
    console.print(f"  why_matters: {info.get('why_matters')}")
    console.print("[bold]Link commands[/bold]")
    for c in info.get("link_commands", []):
        console.print(f"  [dim]{c}[/dim]")
    console.print("[dim]inbox accept --id " + item_id + "  |  inbox reject --id " + item_id + "  |  inbox defer --id " + item_id + "[/dim]")


def cmd_inbox_accept(item_id: str, note: str = "", repo_root: str = "") -> None:
    from rich.console import Console
    console = Console()
    root = _root(repo_root)
    result = accept_item(item_id, note=note, repo_root=root)
    if result.get("error"):
        console.print(f"[red]{result['error']}[/red]")
        return
    console.print(f"[green]Accepted[/green] {item_id}" + (f"  {result.get('note', '')}" if result.get("note") else ""))


def cmd_inbox_reject(item_id: str, note: str = "", repo_root: str = "") -> None:
    from rich.console import Console
    console = Console()
    root = _root(repo_root)
    result = reject_item(item_id, note=note, repo_root=root)
    if result.get("error"):
        console.print(f"[red]{result['error']}[/red]")
        return
    console.print(f"[yellow]Rejected[/yellow] {item_id}" + (f"  {result.get('note', '')}" if result.get("note") else ""))


def cmd_inbox_defer(item_id: str, note: str = "", revisit_after: str = "", repo_root: str = "") -> None:
    from rich.console import Console
    console = Console()
    root = _root(repo_root)
    result = defer_item(item_id, note=note, revisit_after=revisit_after, repo_root=root)
    if result.get("error"):
        console.print(f"[red]{result['error']}[/red]")
        return
    console.print(f"[yellow]Deferred[/yellow] {item_id}" + (f"  revisit_after={revisit_after}" if revisit_after else "") + (f"  {result.get('note', '')}" if result.get("note") else ""))


# M29L.1 Digest views
def cmd_digest_morning(repo_root: str = "", limit: int = 25) -> None:
    from rich.console import Console
    from workflow_dataset.review_studio.digests import build_morning_summary, format_digest_view
    console = Console()
    root = _root(repo_root)
    digest = build_morning_summary(repo_root=root, timeline_limit=limit)
    console.print(format_digest_view(digest))


def cmd_digest_end_of_day(repo_root: str = "", limit: int = 40) -> None:
    from rich.console import Console
    from workflow_dataset.review_studio.digests import build_end_of_day_summary, format_digest_view
    console = Console()
    root = _root(repo_root)
    digest = build_end_of_day_summary(repo_root=root, timeline_limit=limit)
    console.print(format_digest_view(digest))


def cmd_digest_project(project_id: str, repo_root: str = "", limit: int = 30) -> None:
    from rich.console import Console
    from workflow_dataset.review_studio.digests import build_project_summary, format_digest_view
    console = Console()
    root = _root(repo_root)
    digest = build_project_summary(project_id=project_id, repo_root=root, timeline_limit=limit)
    console.print(format_digest_view(digest))


def cmd_digest_rollout_support(repo_root: str = "") -> None:
    from rich.console import Console
    from workflow_dataset.review_studio.digests import build_rollout_support_summary, format_digest_view
    console = Console()
    root = _root(repo_root)
    digest = build_rollout_support_summary(repo_root=root)
    console.print(format_digest_view(digest))

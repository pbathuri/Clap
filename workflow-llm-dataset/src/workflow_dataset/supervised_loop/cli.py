"""
M27E–M27H: CLI for supervised agent loop — status, next, queue, approve, reject, defer, cycle-report.
"""

from __future__ import annotations

from pathlib import Path

from workflow_dataset.supervised_loop.models import AgentCycle, LOOP_STATUS_PROPOSING
from workflow_dataset.supervised_loop.store import load_cycle, save_cycle
from workflow_dataset.supervised_loop.next_action import propose_next_actions
from workflow_dataset.supervised_loop.queue import (
    enqueue_proposal,
    list_pending,
    list_pending_sorted,
    list_deferred,
    get_item,
    approve,
    reject,
    defer,
    revisit_deferred,
    approve_batch,
)
from workflow_dataset.supervised_loop.store import load_operator_policy, save_operator_policy
from workflow_dataset.supervised_loop.models import OperatorPolicy
from workflow_dataset.supervised_loop.handoff import execute_approved
from workflow_dataset.supervised_loop.summary import build_cycle_summary

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

try:
    from workflow_dataset.utils.hashes import stable_id
except Exception:
    def stable_id(*parts: str, prefix: str = "") -> str:
        import hashlib
        return prefix + hashlib.sha256("".join(str(p) for p in parts).encode()).hexdigest()[:16]


def _root(repo_root: str):
    return Path(repo_root).resolve() if repo_root else None


def cmd_status(repo_root: str = "") -> None:
    from rich.console import Console
    console = Console()
    root = _root(repo_root)
    summary = build_cycle_summary(root)
    console.print("[bold]Supervised agent loop[/bold]")
    console.print(f"  cycle_id: {summary.cycle_id or '(none)'}")
    console.print(f"  project: {summary.project_slug or '(none)'}")
    console.print(f"  goal: {(summary.goal_text[:60] + '...') if summary.goal_text and len(summary.goal_text) > 60 else (summary.goal_text or '(none)')}")
    console.print(f"  status: {summary.status or 'idle'}")
    if summary.blocked_reason:
        console.print(f"  blocked: {summary.blocked_reason}")
    console.print(f"  pending: {summary.pending_queue_count}  approved: {summary.approved_count}  rejected: {summary.rejected_count}  deferred: {summary.deferred_count}")
    console.print(f"  last_handoff: {summary.last_handoff_status or '—'}  last_run_id: {summary.last_run_id or '—'}")
    console.print(f"  next_proposed: {summary.next_proposed_action_label or '—'}")


def cmd_next(project: str = "", repo_root: str = "") -> dict:
    from rich.console import Console
    console = Console()
    root = _root(repo_root)
    cycle = load_cycle(root)
    if not cycle:
        cycle = AgentCycle(
            cycle_id=stable_id("cy", project or "default", utc_now_iso(), prefix="cy_"),
            project_slug=project or "default",
            goal_text="",
            session_id="",
            status=LOOP_STATUS_PROPOSING,
            created_at=utc_now_iso(),
            updated_at=utc_now_iso(),
        )
        from workflow_dataset.planner.store import load_current_goal
        cycle.goal_text = load_current_goal(root) or ""
        save_cycle(cycle, root)
    proposed, blocked = propose_next_actions(project or cycle.project_slug, root)
    if blocked:
        cycle.blocked_reason = blocked
        cycle.status = "blocked"
        cycle.updated_at = utc_now_iso()
        save_cycle(cycle, root)
        console.print(f"[yellow]Blocked: {blocked.reason}[/yellow]")
        return {"blocked": blocked.reason, "proposed": []}
    if not proposed:
        console.print("[yellow]No proposed actions.[/yellow]")
        return {"proposed": []}
    queue_ids = []
    for act in proposed:
        item = enqueue_proposal(act, cycle.cycle_id, root)
        queue_ids.append(item.queue_id)
        console.print(f"  [green]Queued[/green] {item.queue_id}  {act.label}")
        console.print(f"    why: {act.why}  risk: {act.risk_level}  mode: {act.mode}")
    return {"proposed": [a.action_id for a in proposed], "queue_ids": queue_ids}


def cmd_queue(repo_root: str = "") -> None:
    from rich.console import Console
    console = Console()
    root = _root(repo_root)
    policy = load_operator_policy(root)
    pending = list_pending_sorted(root, policy)
    if not pending:
        console.print("No pending items in approval queue.")
        return
    console.print("[bold]Approval queue (pending)[/bold] [dim]sorted: manual-review first, then by risk, then created[/dim]")
    for q in pending:
        a = q.action
        manual = " [manual review]" if policy.requires_manual_review(a) else ""
        console.print(f"  [bold]{q.queue_id}[/bold]  {a.label}{manual}")
        console.print(f"    type={a.action_type}  plan_ref={a.plan_ref}  mode={a.mode}  risk={a.risk_level}")
        console.print(f"    why: {a.why}")
        console.print("    [dim]approve: workflow-dataset agent-loop approve --id " + q.queue_id + "[/dim]")
    console.print("[dim]Batch (low-risk only): workflow-dataset agent-loop approve-batch --max-risk low[/dim]")


def cmd_approve(queue_id: str, note: str = "", repo_root: str = "", run_after: bool = True) -> dict:
    from rich.console import Console
    console = Console()
    root = _root(repo_root)
    item = approve(queue_id, note, root)
    if not item:
        console.print(f"[red]Not found or not pending: {queue_id}[/red]")
        return {"error": "not found or not pending"}
    console.print(f"[green]Approved[/green] {queue_id}")
    if run_after:
        result = execute_approved(queue_id, root)
        if result.get("error"):
            console.print(f"[red]{result['error']}[/red]")
        else:
            console.print(f"  handoff_id: {result.get('handoff_id')}  status: {result.get('status')}  run_id: {result.get('run_id', '')}")
            if result.get("outcome_summary"):
                console.print(f"  outcome: {result['outcome_summary']}")
        return result
    return {"approved": queue_id}


def cmd_reject(queue_id: str, note: str = "", repo_root: str = "") -> None:
    from rich.console import Console
    console = Console()
    root = _root(repo_root)
    item = reject(queue_id, note, root)
    if not item:
        console.print(f"[red]Not found or not pending: {queue_id}[/red]")
        return
    console.print(f"[yellow]Rejected[/yellow] {queue_id}")


def cmd_defer(
    queue_id: str,
    note: str = "",
    repo_root: str = "",
    defer_reason: str = "",
    revisit_after: str = "",
) -> None:
    from rich.console import Console
    console = Console()
    root = _root(repo_root)
    item = defer(queue_id, note, root, defer_reason=defer_reason, revisit_after=revisit_after)
    if not item:
        console.print(f"[red]Not found or not pending: {queue_id}[/red]")
        return
    console.print(f"[dim]Deferred[/dim] {queue_id}")
    if defer_reason:
        console.print(f"  reason: {defer_reason}")
    if revisit_after:
        console.print(f"  revisit_after: {revisit_after}")
    console.print("  [dim]Revisit: workflow-dataset agent-loop revisit --id " + queue_id + "[/dim]")


def cmd_list_deferred(repo_root: str = "") -> None:
    from rich.console import Console
    console = Console()
    root = _root(repo_root)
    deferred = list_deferred(root)
    if not deferred:
        console.print("No deferred items.")
        return
    console.print("[bold]Deferred items[/bold]")
    for q in deferred:
        a = q.action
        console.print(f"  {q.queue_id}  {a.label}")
        console.print(f"    defer_reason: {q.defer_reason or q.decision_note or '—'}  revisit_after: {q.revisit_after or '—'}")
        console.print("    [dim]revisit: workflow-dataset agent-loop revisit --id " + q.queue_id + "[/dim]")


def cmd_revisit(queue_id: str, repo_root: str = "") -> None:
    from rich.console import Console
    console = Console()
    root = _root(repo_root)
    item = revisit_deferred(queue_id, root)
    if not item:
        console.print(f"[red]Not found or not deferred: {queue_id}[/red]")
        return
    console.print(f"[green]Requeued[/green] {queue_id} (back to pending)")


def cmd_approve_batch(
    max_risk: str = "low",
    no_execute: bool = False,
    repo_root: str = "",
) -> dict:
    from rich.console import Console
    console = Console()
    root = _root(repo_root)
    result = approve_batch(max_risk=max_risk, run_after=not no_execute, repo_root=root)
    console.print(f"[bold]Batch approval[/bold]  max_risk={max_risk}  approved={result['approved_count']}")
    if result["approved_ids"]:
        for qid in result["approved_ids"]:
            console.print(f"  [green]Approved[/green] {qid}")
    if result.get("executed"):
        for e in result["executed"]:
            console.print(f"  executed {e['queue_id']}  handoff={e.get('handoff_id')}  status={e.get('status')}")
            if e.get("error"):
                console.print(f"    [red]error: {e['error']}[/red]")
    if result["skipped_manual_review"]:
        console.print(f"  [dim]Skipped (manual review): {result['skipped_manual_review']}[/dim]")
    if result["skipped_risk"]:
        console.print(f"  [dim]Skipped (risk): {result['skipped_risk']}[/dim]")
    return result


def cmd_policy_show(repo_root: str = "") -> None:
    from rich.console import Console
    console = Console()
    root = _root(repo_root)
    policy = load_operator_policy(root)
    console.print("[bold]Operator policy[/bold]")
    console.print(f"  batch_approve_max_risk: {policy.batch_approve_max_risk}")
    console.print(f"  auto_queue_action_types: {policy.auto_queue_action_types}")
    console.print(f"  always_manual_review_action_types: {policy.always_manual_review_action_types}")
    console.print(f"  always_manual_review_risk_levels: {policy.always_manual_review_risk_levels}")
    console.print(f"  always_manual_review_modes: {policy.always_manual_review_modes}")
    console.print(f"  defer_revisit_max_days: {policy.defer_revisit_max_days}")
    console.print("  [dim]Edit: data/local/supervised_loop/operator_policy.json[/dim]")


def cmd_cycle_report(latest: bool = True, repo_root: str = "") -> None:
    from rich.console import Console
    console = Console()
    root = _root(repo_root)
    summary = build_cycle_summary(root)
    console.print("[bold]=== Cycle report ===[/bold]")
    console.print(f"cycle_id: {summary.cycle_id or '(none)'}")
    console.print(f"project: {summary.project_slug or '(none)'}")
    console.print(f"goal: {summary.goal_text or '(none)'}")
    console.print(f"status: {summary.status or 'idle'}")
    console.print(f"blocked: {summary.blocked_reason or '—'}")
    console.print(f"pending: {summary.pending_queue_count}  approved: {summary.approved_count}  rejected: {summary.rejected_count}  deferred: {summary.deferred_count}")
    console.print(f"last_handoff: {summary.last_handoff_status}  last_run_id: {summary.last_run_id}")
    console.print(f"next_proposed: {summary.next_proposed_action_label or '—'} (id: {summary.next_proposed_action_id or '—'})")

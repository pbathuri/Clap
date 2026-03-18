"""
M34E–M34H: CLI for bounded background runner — queue, run, status, history, retry, suppress.
"""

from __future__ import annotations

import json
from pathlib import Path

from workflow_dataset.background_run.store import load_queue, load_run, list_runs, load_history, save_queue
from workflow_dataset.background_run.runner import run_one_background, build_run_summary, pick_eligible_job
from workflow_dataset.background_run.recovery import retry_run, suppress_run
from workflow_dataset.background_run.models import QueuedRecurringJob


def _root(repo_root: str | None) -> Path:
    if repo_root:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def cmd_queue(
    repo_root: str = "",
    json_out: bool = False,
    add: str | None = None,
    plan_source: str = "job",
    plan_ref: str = "",
    automation_id: str = "",
) -> None:
    """List queued recurring jobs, or add one (--add automation_id with --plan-ref)."""
    from rich.console import Console
    console = Console()
    root = _root(repo_root or None)
    if add:
        if not plan_ref:
            console.print("[red]--add requires --plan-ref[/red]")
            return
        try:
            from workflow_dataset.utils.dates import utc_now_iso
        except Exception:
            from datetime import datetime, timezone
            def utc_now_iso() -> str:
                return datetime.now(timezone.utc).isoformat()
        job = QueuedRecurringJob(
            automation_id=automation_id or add,
            plan_source=plan_source,
            plan_ref=plan_ref,
            trigger_type="manual",
            allowed_modes=["simulate"],
            require_approval_before_real=True,
            label=f"{plan_source}:{plan_ref}",
            created_at=utc_now_iso(),
            last_queued_at=utc_now_iso(),
        )
        jobs = load_queue(root)
        jobs.append(job)
        save_queue(jobs, root)
        console.print(f"[green]Queued[/green] {job.automation_id}  plan_ref={plan_ref}")
        return
    jobs = load_queue(root)
    if json_out:
        console.print(json.dumps({"jobs": [j.to_dict() for j in jobs], "count": len(jobs)}, indent=2))
    else:
        if not jobs:
            console.print("[dim]No queued recurring jobs. Add with: workflow-dataset background queue --add <id> --plan-ref <routine_id|job_id>[/dim]")
            return
        console.print("[bold]Queued recurring jobs[/bold]")
        for j in jobs:
            console.print(f"  {j.automation_id}  {j.plan_source}:{j.plan_ref}  modes={j.allowed_modes}")


def cmd_run(
    id: str = "",
    repo_root: str = "",
    json_out: bool = False,
) -> None:
    """Run one background workflow (next eligible from queue, or --id automation_id to run that one)."""
    from rich.console import Console
    console = Console()
    root = _root(repo_root or None)
    job = None
    if id:
        for j in load_queue(root):
            if j.automation_id == id:
                job = j
                break
        if not job:
            console.print(f"[red]No queued job with automation_id: {id}[/red]")
            return
    work_state = None
    try:
        from workflow_dataset.context.work_state import build_work_state
        work_state = build_work_state(root)
    except Exception:
        pass
    result = run_one_background(job=job, work_state=work_state, simulate_first=True, allow_real_after_simulate=False, repo_root=root)
    if json_out:
        console.print(json.dumps(result, indent=2))
    else:
        if result.get("error"):
            console.print(f"[red]{result['error']}[/red]")
        console.print(f"  run_id: {result.get('run_id', '')}  status: {result.get('status', '')}")
        if result.get("outcome_summary"):
            console.print(f"  outcome: {result['outcome_summary']}")


def cmd_status(repo_root: str = "", json_out: bool = False) -> None:
    """Show background runner status: active, blocked, retryable, next, queue length."""
    from rich.console import Console
    console = Console()
    root = _root(repo_root or None)
    summary = build_run_summary(repo_root=root)
    if json_out:
        console.print(json.dumps({
            "active_run_ids": summary.active_run_ids,
            "blocked_run_ids": summary.blocked_run_ids,
            "retryable_run_ids": summary.retryable_run_ids,
            "next_automation_id": summary.next_automation_id,
            "next_plan_ref": summary.next_plan_ref,
            "queue_length": summary.queue_length,
            "recent_outcomes": summary.recent_outcomes[:5],
            "needs_review_automation_ids": summary.needs_review_automation_ids,
        }, indent=2))
    else:
        console.print("[bold]Background runner status[/bold]")
        console.print(f"  queue: {summary.queue_length}  next: {summary.next_automation_id or '—'} ({summary.next_plan_ref or '—'})")
        console.print(f"  active: {len(summary.active_run_ids)}  blocked: {len(summary.blocked_run_ids)}  retryable: {len(summary.retryable_run_ids)}")
        if summary.needs_review_automation_ids:
            console.print(f"  needs_review: {', '.join(summary.needs_review_automation_ids[:5])}")


def cmd_history(repo_root: str = "", limit: int = 20, json_out: bool = False) -> None:
    """Show recent background run history."""
    from rich.console import Console
    console = Console()
    root = _root(repo_root or None)
    entries = load_history(limit=limit, repo_root=root)
    if json_out:
        console.print(json.dumps({"entries": entries}, indent=2))
    else:
        console.print("[bold]Background run history[/bold]")
        for e in entries[:limit]:
            console.print(f"  {e.get('run_id', '')}  {e.get('status', '')}  {e.get('automation_id', '')}  {e.get('timestamp', '')}")


def cmd_retry(run_id: str, repo_root: str = "", json_out: bool = False, no_backoff: bool = False) -> None:
    """Mark a run for retry (with backoff by default; use --no-backoff to run immediately)."""
    from rich.console import Console
    console = Console()
    root = _root(repo_root or None)
    result = retry_run(run_id, repo_root=root, with_backoff=not no_backoff)
    if json_out:
        console.print(json.dumps(result, indent=2))
    else:
        if result.get("error"):
            console.print(f"[red]{result['error']}[/red]")
        else:
            console.print(f"[green]Retry queued[/green] run_id={result.get('run_id')}  retry_count={result.get('retry_count')}")
            if result.get("defer_until"):
                console.print(f"  defer_until: {result['defer_until']}")


def cmd_suppress(run_id: str, repo_root: str = "", json_out: bool = False) -> None:
    """Suppress a run (do not retry)."""
    from rich.console import Console
    console = Console()
    root = _root(repo_root or None)
    result = suppress_run(run_id, repo_root=root)
    if json_out:
        console.print(json.dumps(result, indent=2))
    else:
        if result.get("error"):
            console.print(f"[red]{result['error']}[/red]")
        else:
            console.print(f"[dim]Suppressed[/dim] run_id={result.get('run_id')}")


def cmd_retry_policy(repo_root: str = "", json_out: bool = False, automation_id: str = "") -> None:
    """Show effective retry policy (default or for --automation-id)."""
    from rich.console import Console
    from workflow_dataset.background_run.retry_policies import get_policy_for_automation
    console = Console()
    root = _root(repo_root or None)
    policy = get_policy_for_automation(automation_id or "", root)
    if json_out:
        console.print(json.dumps(policy.to_dict(), indent=2))
    else:
        console.print("[bold]Retry policy[/bold]" + (f" (automation: {automation_id})" if automation_id else " (default)"))
        console.print(f"  max_retries: {policy.max_retries}  backoff: {policy.backoff_strategy}  base_seconds: {policy.backoff_base_seconds}")
        console.print(f"  suppress_after_failures: {policy.suppress_after_failures}  handoff_after_failures: {policy.handoff_after_failures}")
        if policy.label:
            console.print(f"  label: {policy.label}")


def cmd_retry_policy_set(
    repo_root: str = "",
    json_out: bool = False,
    default: bool = False,
    automation_id: str = "",
    max_retries: int = 3,
    backoff: str = "exponential",
    base_seconds: int = 60,
    suppress_after: int = 0,
    handoff_after: int = 0,
) -> None:
    """Set retry policy (default or for automation). Saves to data/local/background_run/retry_policies.json."""
    from rich.console import Console
    from workflow_dataset.background_run.models import RetryPolicy
    from workflow_dataset.background_run.store import load_retry_policies, save_retry_policies
    console = Console()
    root = _root(repo_root or None)
    policies = load_retry_policies(root)
    policy = RetryPolicy(
        policy_id="default" if default or not automation_id else automation_id,
        max_retries=max_retries,
        backoff_strategy=backoff,
        backoff_base_seconds=base_seconds,
        suppress_after_failures=suppress_after,
        handoff_after_failures=handoff_after,
        label=f"max_retries={max_retries} backoff={backoff}",
    )
    if automation_id:
        by_automation = dict(policies.get("by_automation") or {})
        by_automation[automation_id] = policy
        save_retry_policies(default=policies.get("default"), by_automation=by_automation, repo_root=root)
    else:
        save_retry_policies(default=policy, by_automation=policies.get("by_automation"), repo_root=root)
    if json_out:
        console.print(json.dumps(policy.to_dict(), indent=2))
    else:
        console.print(f"[green]Saved[/green] retry policy (default={default} automation_id={automation_id or '—'})")


def cmd_fallback_report(repo_root: str = "", limit: int = 20, json_out: bool = False) -> None:
    """Show degraded fallback report: failed/blocked/deferred runs with failure code and operator explanation."""
    from rich.console import Console
    from workflow_dataset.background_run.degraded_fallback import build_degraded_fallback_report
    console = Console()
    root = _root(repo_root or None)
    report = build_degraded_fallback_report(limit=limit, repo_root=root)
    if json_out:
        console.print(json.dumps(report, indent=2))
    else:
        console.print("[bold]Degraded fallback report[/bold]")
        for e in report.get("entries", []):
            console.print(f"  {e.get('run_id', '')}  {e.get('status', '')}  {e.get('failure_code', '')}  {e.get('fallback_profile_id', '')}")
            if e.get("operator_explanation"):
                msg = e["operator_explanation"]
                console.print(f"    {(msg[:77] + '...') if len(msg) > 80 else msg}")
        if not report.get("entries"):
            console.print("[dim]No failed/blocked/deferred runs.[/dim]")


def cmd_explain(run_id: str, repo_root: str = "", json_out: bool = False) -> None:
    """Explain why a run failed and what fallback applies (operator-facing)."""
    from rich.console import Console
    from workflow_dataset.background_run.explain import build_failure_explanation, build_fallback_explanation
    console = Console()
    root = _root(repo_root or None)
    run = load_run(run_id, root)
    if not run:
        console.print(f"[red]Run not found: {run_id}[/red]")
        return
    failure_expl = build_failure_explanation(run)
    fallback_expl = build_fallback_explanation(run)
    if json_out:
        console.print(json.dumps({"failure": failure_expl, "fallback": fallback_expl}, indent=2))
    else:
        console.print("[bold]Failure[/bold]")
        console.print(f"  {failure_expl.get('summary', '')}")
        console.print("[bold]Fallback[/bold]")
        console.print(f"  {fallback_expl.get('operator_explanation', '')}")
        if fallback_expl.get("recommended_action"):
            console.print(f"  -> {fallback_expl['recommended_action']}")

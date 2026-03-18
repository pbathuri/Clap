"""
M46E–M46H: Maintenance control flow — propose, review, approve, execute, verify, escalate, rollback.
"""

from __future__ import annotations

import subprocess
import time
from pathlib import Path
from typing import Any

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

from workflow_dataset.repair_loops.models import (
    RepairLoop,
    RepairLoopStatus,
    BoundedRepairPlan,
    RepairResult,
    PostRepairVerification,
    RollbackOnFailedRepair,
    RequiredReviewGate,
    ReviewGateKind,
    MaintenanceAction,
)
from workflow_dataset.repair_loops.store import save_repair_loop, load_repair_loop


def _stable_id(prefix: str, *parts: str) -> str:
    import hashlib
    raw = "_".join(str(p) for p in parts if p)
    h = hashlib.sha256(raw.encode()).hexdigest()[:12]
    return f"{prefix}_{h}"


def _guidance_for_proposal(
    pattern_id: str,
    maintenance_profile_id: str,
    repair_bundle_id: str,
) -> "RepairGuidance | None":
    """M46H.1: Build operator guidance from profile and optional bundle."""
    from workflow_dataset.repair_loops.models import RepairGuidance, RepairGuidanceKind
    from workflow_dataset.repair_loops.profiles import get_maintenance_profile
    from workflow_dataset.repair_loops.bundles import get_safe_repair_bundle
    profile = get_maintenance_profile(maintenance_profile_id) if maintenance_profile_id else None
    bundle = get_safe_repair_bundle(repair_bundle_id) if repair_bundle_id else None
    if not profile and not bundle:
        return None
    guidance = None
    if profile and pattern_id:
        if profile.is_pattern_allowed(pattern_id):
            guidance = profile.guidance_for_pattern(pattern_id)
    if not guidance and bundle:
        guidance = RepairGuidance(
            kind=RepairGuidanceKind.do_now,
            reason=bundle.do_now_guidance or bundle.operator_summary,
        )
    if guidance and bundle:
        if guidance.kind == RepairGuidanceKind.do_now and bundle.do_now_guidance:
            guidance = RepairGuidance(kind=guidance.kind, reason=bundle.do_now_guidance, suggested_schedule=guidance.suggested_schedule)
        elif guidance.kind == RepairGuidanceKind.schedule_later and bundle.schedule_later_guidance:
            guidance = RepairGuidance(kind=guidance.kind, reason=bundle.schedule_later_guidance, suggested_schedule=guidance.suggested_schedule)
    return guidance


def propose_repair_plan(
    plan: BoundedRepairPlan,
    source_signal_id: str = "",
    source_signal_type: str = "",
    maintenance_profile_id: str = "",
    repair_bundle_id: str = "",
    pattern_id: str = "",
    repo_root: Path | str | None = None,
) -> RepairLoop:
    """Create a new repair loop in proposed state. M46H.1: Optional profile/bundle set operator guidance."""
    repair_loop_id = _stable_id("rl", plan.plan_id, source_signal_id, utc_now_iso())
    pid = pattern_id or plan.plan_id
    guidance = _guidance_for_proposal(pid, maintenance_profile_id, repair_bundle_id)
    loop = RepairLoop(
        repair_loop_id=repair_loop_id,
        plan=plan,
        status=RepairLoopStatus.proposed,
        source_signal_id=source_signal_id,
        source_signal_type=source_signal_type,
        created_at=utc_now_iso(),
        updated_at=utc_now_iso(),
        maintenance_profile_id=maintenance_profile_id,
        repair_bundle_id=repair_bundle_id,
        operator_guidance=guidance,
    )
    save_repair_loop(loop, repo_root)
    return loop


def review_repair_plan(
    repair_loop_id: str,
    repo_root: Path | str | None = None,
) -> RepairLoop | None:
    """Mark repair loop as under_review (no state change to plan; caller performs review)."""
    loop = load_repair_loop(repair_loop_id, repo_root)
    if not loop or loop.status not in (RepairLoopStatus.proposed, RepairLoopStatus.under_review):
        return None
    loop.status = RepairLoopStatus.under_review
    loop.updated_at = utc_now_iso()
    save_repair_loop(loop, repo_root)
    return loop


def approve_bounded_repair(
    repair_loop_id: str,
    approved_by: str = "operator",
    repo_root: Path | str | None = None,
) -> RepairLoop | None:
    """Approve repair loop; set review gate passed and status to approved."""
    loop = load_repair_loop(repair_loop_id, repo_root)
    if not loop or loop.status not in (RepairLoopStatus.proposed, RepairLoopStatus.under_review):
        return None
    gate = loop.plan.required_review_gate
    if gate:
        gate.passed = True
        gate.passed_at = utc_now_iso()
        gate.passed_by = approved_by
    loop.status = RepairLoopStatus.approved
    loop.approved_at = utc_now_iso()
    loop.approved_by = approved_by
    loop.updated_at = utc_now_iso()
    save_repair_loop(loop, repo_root)
    return loop


def _run_command(
    run_command: str,
    run_command_args: list[str],
    repo_root: Path | str | None,
) -> tuple[bool, str, float]:
    """Run a repair command via workflow-dataset CLI. Returns (success, output, duration_seconds)."""
    root = Path(repo_root).resolve() if repo_root else None
    cmd = ["workflow-dataset", run_command] + list(run_command_args)
    if root:
        cmd.extend(["--repo-root", str(root)])
    start = time.perf_counter()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
            cwd=str(root) if root else None,
        )
        duration = time.perf_counter() - start
        out = (result.stdout or "").strip() + "\n" + (result.stderr or "").strip()
        return result.returncode == 0, out or str(result.returncode), duration
    except subprocess.TimeoutExpired:
        duration = time.perf_counter() - start
        return False, "timeout", duration
    except FileNotFoundError:
        duration = time.perf_counter() - start
        return False, "workflow-dataset not found (run from env)", duration
    except Exception as e:
        duration = time.perf_counter() - start
        return False, str(e), duration


def _execute_action(
    action: MaintenanceAction,
    repo_root: Path | str | None,
) -> RepairResult:
    """Execute a single maintenance action via workflow-dataset CLI: <run_command> <run_command_args>."""
    result_id = _stable_id("res", action.action_id, utc_now_iso())
    root = Path(repo_root).resolve() if repo_root else None
    full_cmd = ["workflow-dataset", action.run_command] + (action.run_command_args or [])
    if root:
        full_cmd.extend(["--repo-root", str(root)])
    start = time.perf_counter()
    try:
        result = subprocess.run(
            full_cmd,
            capture_output=True,
            text=True,
            timeout=300,
            cwd=str(root) if root else None,
        )
        duration = time.perf_counter() - start
        out = (result.stdout or "").strip() + "\n" + (result.stderr or "").strip()
        success = result.returncode == 0
    except subprocess.TimeoutExpired:
        duration = time.perf_counter() - start
        out = "timeout"
        success = False
    except FileNotFoundError:
        duration = time.perf_counter() - start
        out = "workflow-dataset not found"
        success = False
    except Exception as e:
        duration = time.perf_counter() - start
        out = str(e)
        success = False
    return RepairResult(
        result_id=result_id,
        plan_id=action.action_id,
        action_id=action.action_id,
        success=success,
        details="",
        output=out,
        duration_seconds=duration,
        timestamp=utc_now_iso(),
    )


def execute_bounded_repair(
    repair_loop_id: str,
    repo_root: Path | str | None = None,
) -> RepairLoop | None:
    """Execute all actions in the approved plan; set status to verifying or failed."""
    loop = load_repair_loop(repair_loop_id, repo_root)
    if not loop or loop.status != RepairLoopStatus.approved:
        return None
    loop.status = RepairLoopStatus.executing
    loop.executed_at = utc_now_iso()
    loop.updated_at = utc_now_iso()
    loop.results = []
    save_repair_loop(loop, repo_root)
    all_ok = True
    for action in loop.plan.actions:
        res = _execute_action(action, repo_root)
        res.plan_id = loop.plan.plan_id
        loop.results.append(res)
        if not res.success:
            all_ok = False
            if loop.plan.rollback_on_failed_repair:
                loop.status = RepairLoopStatus.failed
                loop.updated_at = utc_now_iso()
                save_repair_loop(loop, repo_root)
                return loop
    loop.status = RepairLoopStatus.verifying
    loop.updated_at = utc_now_iso()
    save_repair_loop(loop, repo_root)
    return loop


def verify_repair(
    repair_loop_id: str,
    repo_root: Path | str | None = None,
) -> RepairLoop | None:
    """Run post-repair verification; set status to verified or failed."""
    loop = load_repair_loop(repair_loop_id, repo_root)
    if not loop or loop.status not in (RepairLoopStatus.verifying, RepairLoopStatus.executing):
        return None
    ver_cmd = loop.plan.verification_command
    ver_args = loop.plan.verification_args or []
    passed = True
    details = ""
    run_output = ""
    if ver_cmd:
        if ver_cmd == "reliability_run":
            success, out, _ = _run_command("reliability", ["run", "--id"] + (ver_args or ["golden_first_run"]), repo_root)
        else:
            success, out, _ = _run_command(ver_cmd, ver_args, repo_root)
        passed = success
        run_output = out
        details = "verified" if success else "verification failed"
    loop.verification = PostRepairVerification(
        verification_id=_stable_id("ver", repair_loop_id, utc_now_iso()),
        plan_id=loop.plan.plan_id,
        passed=passed,
        details=details,
        run_command=ver_cmd,
        run_output=run_output,
        timestamp=utc_now_iso(),
    )
    loop.status = RepairLoopStatus.verified if passed else RepairLoopStatus.failed
    loop.updated_at = utc_now_iso()
    save_repair_loop(loop, repo_root)
    return loop


def escalate_if_failed(
    repair_loop_id: str,
    reason: str = "",
    repo_root: Path | str | None = None,
) -> RepairLoop | None:
    """Mark a failed repair as escalated (for council/recovery)."""
    loop = load_repair_loop(repair_loop_id, repo_root)
    if not loop:
        return None
    if loop.status != RepairLoopStatus.failed and loop.status != RepairLoopStatus.rolled_back:
        return None
    loop.status = RepairLoopStatus.escalated
    loop.escalation_reason = reason or "Repair failed; escalation to " + (loop.plan.escalation_target or "support")
    loop.updated_at = utc_now_iso()
    save_repair_loop(loop, repo_root)
    return loop


def rollback_if_needed(
    repair_loop_id: str,
    repo_root: Path | str | None = None,
) -> RepairLoop | None:
    """Execute rollback for actions that have rollback_command; set status to rolled_back."""
    loop = load_repair_loop(repair_loop_id, repo_root)
    if not loop or loop.status != RepairLoopStatus.failed:
        return None
    rolled: list[str] = []
    success = True
    for action in reversed(loop.plan.actions):
        if not action.rollback_command:
            continue
        res = _execute_action(
            MaintenanceAction(
                action_id=action.action_id + "_rollback",
                name=action.name + " (rollback)",
                run_command=action.rollback_command,
                run_command_args=action.rollback_args,
            ),
            repo_root,
        )
        rolled.append(action.action_id)
        if not res.success:
            success = False
    loop.rollback = RollbackOnFailedRepair(
        rollback_id=_stable_id("rb", repair_loop_id, utc_now_iso()),
        plan_id=loop.plan.plan_id,
        actions_rolled_back=rolled,
        success=success,
        details="Rollback completed" if success else "Some rollbacks failed",
        timestamp=utc_now_iso(),
    )
    loop.status = RepairLoopStatus.rolled_back
    loop.updated_at = utc_now_iso()
    save_repair_loop(loop, repo_root)
    return loop

"""
M23V/M23P: Macro preview and checkpointed run. Uses copilot plan/run; macro = routine 1:1. M23P: stop-at-checkpoints, resume.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

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
        return prefix + hashlib.sha256("".join(parts).encode()).hexdigest()[:16]

from workflow_dataset.macros.schema import Macro, MacroStep, STEP_TYPE_TRUSTED_REAL
from workflow_dataset.macros.step_classifier import classify_step
from workflow_dataset.macros.run_state import (
    save_run_state,
    load_run_state,
    list_paused_runs,
    list_awaiting_approval_runs,
    list_all_macro_runs,
    STATUS_AWAITING_APPROVAL,
    STATUS_BLOCKED,
    STATUS_COMPLETED,
    STATUS_PAUSED,
)
from workflow_dataset.copilot.routines import list_routines, get_routine, get_ordered_job_ids
from workflow_dataset.copilot.plan import build_plan_for_routine, PlanPreview
from workflow_dataset.copilot.run import run_plan, list_plan_runs
from workflow_dataset.copilot.config import get_runs_dir
from workflow_dataset.job_packs import get_job_pack, run_job, load_specialization
from workflow_dataset.job_packs.execute import resolve_params


def _macro_from_routine(routine_id: str, repo_root: Path | None) -> Macro | None:
    r = get_routine(routine_id, repo_root)
    if not r:
        return None
    job_ids = get_ordered_job_ids(r)
    return Macro(
        macro_id=routine_id,
        title=r.title,
        description=r.description or "",
        routine_id=routine_id,
        job_pack_ids=job_ids,
        mode="real" if not r.simulate_only else "simulate",
        stop_on_first_blocked=r.stop_on_first_blocked,
        required_approvals=list(r.required_approvals),
        simulate_only=r.simulate_only,
        checkpoint_after_step_indices=[],
        stop_conditions=[],
        expected_outputs=list(getattr(r, "expected_outputs", []) or []),
    )


def list_macros(repo_root: Path | str | None = None) -> list[Macro]:
    """List macros (one per routine)."""
    root = Path(repo_root).resolve() if repo_root else None
    out: list[Macro] = []
    for rid in list_routines(root):
        m = _macro_from_routine(rid, root)
        if m:
            out.append(m)
    return out


def macro_preview(macro_id: str, mode: str = "simulate", repo_root: Path | str | None = None) -> PlanPreview | None:
    """Build plan preview for macro (routine). No execution."""
    root = Path(repo_root).resolve() if repo_root else None
    return build_plan_for_routine(macro_id, mode, repo_root=root)


def get_macro_steps(macro_id: str, mode: str = "simulate", repo_root: Path | str | None = None) -> list[MacroStep]:
    """M23P: Return classified steps for macro (routine). No execution."""
    root = Path(repo_root).resolve() if repo_root else None
    routine = get_routine(macro_id, root)
    if not routine:
        return []
    job_ids = get_ordered_job_ids(routine)
    return [classify_step(jid, mode, root) for jid in job_ids]


def macro_run(
    macro_id: str,
    mode: str = "simulate",
    repo_root: Path | str | None = None,
    stop_on_first_blocked: bool = True,
    continue_on_blocked: bool = False,
    stop_at_checkpoints: bool = False,
) -> dict[str, Any]:
    """
    Run macro (routine): build plan, run. If stop_at_checkpoints, pause after checkpoint steps and persist state for resume.
    """
    root = Path(repo_root).resolve() if repo_root else None
    if stop_at_checkpoints:
        return _run_macro_checkpointed(
            macro_id, mode, root,
            stop_on_first_blocked=stop_on_first_blocked,
            continue_on_blocked=continue_on_blocked,
        )
    plan = build_plan_for_routine(macro_id, mode, repo_root=root)
    if not plan:
        return {"error": f"Macro not found or invalid: {macro_id}"}
    return run_plan(plan, repo_root=root, stop_on_first_blocked=stop_on_first_blocked, continue_on_blocked=continue_on_blocked)


def _run_macro_checkpointed(
    macro_id: str,
    mode: str,
    root: Path | None,
    stop_on_first_blocked: bool = True,
    continue_on_blocked: bool = False,
) -> dict[str, Any]:
    """Execute macro step-by-step; pause at checkpoints and persist state."""
    plan = build_plan_for_routine(macro_id, mode, repo_root=root)
    if not plan:
        return {"error": f"Macro not found or invalid: {macro_id}"}
    macro = _macro_from_routine(macro_id, root)
    job_ids = plan.job_pack_ids
    run_id = stable_id("macro", macro_id, plan.plan_id, utc_now_iso(), prefix="")[:20]
    runs_dir = get_runs_dir(root)
    run_path = runs_dir / run_id
    run_path.mkdir(parents=True, exist_ok=True)

    executed: list[dict[str, Any]] = []
    blocked_steps: list[dict[str, Any]] = []
    errors: list[str] = []
    checkpoint_after = set((macro.checkpoint_after_step_indices or []))

    for i, jid in enumerate(job_ids):
        if jid in plan.blocked:
            blocked_steps.append({
                "job_pack_id": jid,
                "reason": plan.blocked_reasons.get(jid, "blocked"),
            })
            if stop_on_first_blocked and not continue_on_blocked:
                save_run_state(
                    run_id, macro_id, STATUS_BLOCKED, plan.plan_id, job_ids, mode,
                    i, executed, blocked_steps, str(run_path), root,
                    approval_required_before_step=i,
                    timestamp=utc_now_iso(),
                    errors=errors,
                )
                _write_plan_run_record(run_path, run_id, plan, executed, blocked_steps, errors)
                return _checkpointed_result(run_id, run_path, plan, executed, blocked_steps, errors, STATUS_BLOCKED)
            continue
        job = get_job_pack(jid, root)
        if not job:
            blocked_steps.append({"job_pack_id": jid, "reason": "job not found"})
            if stop_on_first_blocked and not continue_on_blocked:
                save_run_state(
                    run_id, macro_id, STATUS_BLOCKED, plan.plan_id, job_ids, mode,
                    i, executed, blocked_steps, str(run_path), root,
                    approval_required_before_step=i,
                    timestamp=utc_now_iso(),
                    errors=errors,
                )
                _write_plan_run_record(run_path, run_id, plan, executed, blocked_steps, errors)
                return _checkpointed_result(run_id, run_path, plan, executed, blocked_steps, errors, STATUS_BLOCKED)
            continue
        spec = load_specialization(jid, root)
        params = resolve_params(job, spec.preferred_params if spec else {}, {})
        result = run_job(jid, mode, params, root, update_specialization_on_success=False)
        if result.get("error"):
            errors.append(f"{jid}: {result['error']}")
            blocked_steps.append({"job_pack_id": jid, "reason": result["error"]})
            if stop_on_first_blocked and not continue_on_blocked:
                save_run_state(
                    run_id, macro_id, STATUS_BLOCKED, plan.plan_id, job_ids, mode,
                    i, executed, blocked_steps, str(run_path), root,
                    approval_required_before_step=i,
                    timestamp=utc_now_iso(),
                    errors=errors,
                )
                _write_plan_run_record(run_path, run_id, plan, executed, blocked_steps, errors)
                return _checkpointed_result(run_id, run_path, plan, executed, blocked_steps, errors, STATUS_BLOCKED)
            continue
        executed.append({
            "job_pack_id": jid,
            "outcome": result.get("outcome"),
            "run_id": result.get("run_id"),
        })
        # Pause after this step if it's a checkpoint or before next trusted_real
        next_step_index = i + 1
        should_pause = (
            (i in checkpoint_after)
            or (mode == "real" and next_step_index < len(job_ids) and classify_step(job_ids[next_step_index], mode, root).step_type == STEP_TYPE_TRUSTED_REAL)
        )
        if should_pause and next_step_index < len(job_ids):
            save_run_state(
                run_id, macro_id, STATUS_AWAITING_APPROVAL, plan.plan_id, job_ids, mode,
                next_step_index, executed, blocked_steps, str(run_path), root,
                approval_required_before_step=next_step_index,
                timestamp=utc_now_iso(),
                errors=errors,
            )
            _write_plan_run_record(run_path, run_id, plan, executed, blocked_steps, errors)
            return _checkpointed_result(
                run_id, run_path, plan, executed, blocked_steps, errors,
                STATUS_AWAITING_APPROVAL,
                message="Paused for approval before next step. Use: workflow-dataset macro resume --run-id " + run_id,
            )
    save_run_state(
        run_id, macro_id, STATUS_COMPLETED, plan.plan_id, job_ids, mode,
        len(job_ids), executed, blocked_steps, str(run_path), root,
        timestamp=utc_now_iso(),
        errors=errors,
    )
    _write_plan_run_record(run_path, run_id, plan, executed, blocked_steps, errors)
    return _checkpointed_result(run_id, run_path, plan, executed, blocked_steps, errors, STATUS_COMPLETED)


def _write_plan_run_record(
    run_path: Path,
    run_id: str,
    plan: PlanPreview,
    executed: list[dict],
    blocked: list[dict],
    errors: list[str],
) -> None:
    record = {
        "plan_run_id": run_id,
        "plan_id": plan.plan_id,
        "job_pack_ids": plan.job_pack_ids,
        "mode": plan.mode,
        "timestamp": utc_now_iso(),
        "executed": executed,
        "blocked": blocked,
        "errors": errors,
        "run_path": str(run_path),
    }
    (run_path / "plan_run.json").write_text(json.dumps(record, indent=2), encoding="utf-8")


def _checkpointed_result(
    run_id: str,
    run_path: Path,
    plan: PlanPreview,
    executed: list,
    blocked: list,
    errors: list,
    status: str,
    message: str = "",
) -> dict[str, Any]:
    out = {
        "plan_run_id": run_id,
        "run_path": str(run_path),
        "plan_id": plan.plan_id,
        "mode": plan.mode,
        "macro_run_status": status,
        "executed_count": len(executed),
        "blocked_count": len(blocked),
        "errors": errors,
    }
    if message:
        out["message"] = message
    return out


def resume_macro_run(run_id: str, repo_root: Path | str | None = None) -> dict[str, Any]:
    """Resume a paused or awaiting_approval macro run from current_step_index."""
    root = Path(repo_root).resolve() if repo_root else None
    state = load_run_state(run_id, root)
    if not state:
        return {"error": f"Run not found or not a checkpointed run: {run_id}"}
    if state.get("status") not in (STATUS_PAUSED, STATUS_AWAITING_APPROVAL):
        return {"error": f"Run {run_id} is not paused (status={state.get('status')}). Nothing to resume."}
    macro_id = state["macro_id"]
    plan_id = state["plan_id"]
    job_ids = state["job_pack_ids"]
    mode = state["mode"]
    current = state["current_step_index"]
    plan = build_plan_for_routine(macro_id, mode, repo_root=root)
    if not plan:
        return {"error": f"Macro {macro_id} not found."}
    run_path = Path(state.get("run_path", get_runs_dir(root) / run_id))
    run_path.mkdir(parents=True, exist_ok=True)
    executed = list(state.get("executed") or [])
    blocked_steps = list(state.get("blocked") or [])
    errors = list(state.get("errors") or [])
    macro = _macro_from_routine(macro_id, root)
    checkpoint_after = set((macro.checkpoint_after_step_indices or []))

    for i in range(current, len(job_ids)):
        jid = job_ids[i]
        if jid in plan.blocked:
            blocked_steps.append({
                "job_pack_id": jid,
                "reason": plan.blocked_reasons.get(jid, "blocked"),
            })
            save_run_state(
                run_id, macro_id, STATUS_BLOCKED, plan_id, job_ids, mode,
                i, executed, blocked_steps, str(run_path), root,
                approval_required_before_step=i,
                timestamp=utc_now_iso(),
                errors=errors,
            )
            _write_plan_run_record(run_path, run_id, plan, executed, blocked_steps, errors)
            return _checkpointed_result(run_id, run_path, plan, executed, blocked_steps, errors, STATUS_BLOCKED)
        job = get_job_pack(jid, root)
        if not job:
            blocked_steps.append({"job_pack_id": jid, "reason": "job not found"})
            save_run_state(
                run_id, macro_id, STATUS_BLOCKED, plan_id, job_ids, mode,
                i, executed, blocked_steps, str(run_path), root,
                approval_required_before_step=i,
                timestamp=utc_now_iso(),
                errors=errors,
            )
            _write_plan_run_record(run_path, run_id, plan, executed, blocked_steps, errors)
            return _checkpointed_result(run_id, run_path, plan, executed, blocked_steps, errors, STATUS_BLOCKED)
        spec = load_specialization(jid, root)
        params = resolve_params(job, spec.preferred_params if spec else {}, {})
        result = run_job(jid, mode, params, root, update_specialization_on_success=False)
        if result.get("error"):
            errors.append(f"{jid}: {result['error']}")
            blocked_steps.append({"job_pack_id": jid, "reason": result["error"]})
            save_run_state(
                run_id, macro_id, STATUS_BLOCKED, plan_id, job_ids, mode,
                i, executed, blocked_steps, str(run_path), root,
                approval_required_before_step=i,
                timestamp=utc_now_iso(),
                errors=errors,
            )
            _write_plan_run_record(run_path, run_id, plan, executed, blocked_steps, errors)
            return _checkpointed_result(run_id, run_path, plan, executed, blocked_steps, errors, STATUS_BLOCKED)
        executed.append({
            "job_pack_id": jid,
            "outcome": result.get("outcome"),
            "run_id": result.get("run_id"),
        })
        next_step_index = i + 1
        should_pause = (
            (i in checkpoint_after)
            or (mode == "real" and next_step_index < len(job_ids) and classify_step(job_ids[next_step_index], mode, root).step_type == STEP_TYPE_TRUSTED_REAL)
        )
        if should_pause and next_step_index < len(job_ids):
            save_run_state(
                run_id, macro_id, STATUS_AWAITING_APPROVAL, plan_id, job_ids, mode,
                next_step_index, executed, blocked_steps, str(run_path), root,
                approval_required_before_step=next_step_index,
                timestamp=utc_now_iso(),
                errors=errors,
            )
            _write_plan_run_record(run_path, run_id, plan, executed, blocked_steps, errors)
            return _checkpointed_result(
                run_id, run_path, plan, executed, blocked_steps, errors,
                STATUS_AWAITING_APPROVAL,
                message="Paused for approval before next step. Use: workflow-dataset macro resume --run-id " + run_id,
            )
    save_run_state(
        run_id, macro_id, STATUS_COMPLETED, plan_id, job_ids, mode,
        len(job_ids), executed, blocked_steps, str(run_path), root,
        timestamp=utc_now_iso(),
        errors=errors,
    )
    _write_plan_run_record(run_path, run_id, plan, executed, blocked_steps, errors)
    return _checkpointed_result(run_id, run_path, plan, executed, blocked_steps, errors, STATUS_COMPLETED)


def get_blocked_steps(macro_id: str, run_id: str | None = None, repo_root: Path | str | None = None) -> list[dict[str, Any]]:
    """
    Return blocked steps for macro. If run_id given, from that plan run; else from latest run for this macro.
    """
    root = Path(repo_root).resolve() if repo_root else None
    runs = list_plan_runs(limit=50, repo_root=root)
    # Find runs that match this macro (plan_id often contains routine id; or we match job_pack_ids to routine)
    routine = get_routine(macro_id, root)
    if not routine:
        return []
    job_ids = set(get_ordered_job_ids(routine))
    for r in runs:
        rid = r.get("plan_run_id")
        if run_id and rid != run_id:
            continue
        plan_jobs = r.get("job_pack_ids") or []
        if set(plan_jobs) == job_ids or (not run_id and plan_jobs):
            blocked = r.get("blocked") or []
            return [{"job_pack_id": b.get("job_pack_id"), "reason": b.get("reason", "")} for b in blocked]
        if run_id:
            break
    return []

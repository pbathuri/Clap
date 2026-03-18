"""
M26E–M26H: Checkpointed executor runner. Run plan with simulate-first, stop at checkpoints, persist to executor hub.
Uses existing run_job and approval checks; no new execution paths.
"""

from __future__ import annotations

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
        return prefix + hashlib.sha256("".join(str(p) for p in parts).encode()).hexdigest()[:20]

from workflow_dataset.copilot.plan import build_plan_for_routine, build_plan_for_job, PlanPreview
from workflow_dataset.job_packs import run_job, get_job_pack, load_specialization
from workflow_dataset.job_packs.execute import resolve_params
from workflow_dataset.executor.models import ExecutionRun, ActionEnvelope
from workflow_dataset.executor.mapping import plan_preview_to_envelopes
from workflow_dataset.executor.hub import save_run, load_run, save_artifacts_list, get_executor_runs_dir, record_recovery_decision
from workflow_dataset.macros.schema import STEP_TYPE_TRUSTED_REAL
from workflow_dataset.macros.step_classifier import classify_step


def resolve_plan(
    plan_source: str,
    plan_ref: str,
    mode: str,
    repo_root: Path | str | None = None,
) -> PlanPreview | None:
    """Resolve plan from source and ref. plan_source: routine | job."""
    root = Path(repo_root).resolve() if repo_root else None
    if plan_source == "routine":
        return build_plan_for_routine(plan_ref, mode, repo_root=root)
    if plan_source == "job":
        return build_plan_for_job(plan_ref, mode, repo_root=root)
    return None


def run_with_checkpoints(
    plan_source: str,
    plan_ref: str,
    mode: str,
    repo_root: Path | str | None = None,
    stop_at_checkpoints: bool = True,
    stop_on_first_blocked: bool = True,
    checkpoint_after_indices: list[int] | None = None,
) -> dict[str, Any]:
    """
    Execute plan step-by-step; persist ExecutionRun to executor hub.
    On checkpoint: status=awaiting_approval, persist, return with resume hint.
    On blocked: status=blocked, persist, return.
    """
    root = Path(repo_root).resolve() if repo_root else None
    plan = resolve_plan(plan_source, plan_ref, mode, root)
    if not plan:
        return {"error": f"Plan not found: source={plan_source} ref={plan_ref}"}

    envelopes = plan_preview_to_envelopes(
        plan.plan_id,
        plan.job_pack_ids,
        plan.mode,
        plan.blocked,
        plan.blocked_reasons,
        repo_root=root,
        checkpoint_after_indices=checkpoint_after_indices,
    )
    run_id = stable_id("exec", plan.plan_id, utc_now_iso(), prefix="")[:20]
    run = ExecutionRun(
        run_id=run_id,
        plan_id=plan.plan_id,
        plan_source=plan_source,
        plan_ref=plan_ref,
        mode=mode,
        status="running",
        current_step_index=0,
        envelopes=envelopes,
        executed=[],
        blocked=[],
        artifacts=[],
        checkpoint_decisions=[],
        errors=[],
        run_path="",
        timestamp_start=utc_now_iso(),
        timestamp_end="",
    )
    save_run(run, root)

    for i, jid in enumerate(plan.job_pack_ids):
        run = load_run(run_id, root)
        if not run:
            return {"error": "Run state lost", "run_id": run_id}
        if run.status in ("cancelled", "completed"):
            return _run_result(run)

        run.current_step_index = i
        env = run.envelopes[i] if i < len(run.envelopes) else None

        if jid in plan.blocked or (env and env.blocked_reason):
            reason = plan.blocked_reasons.get(jid, env.blocked_reason if env else "blocked")
            run.blocked.append({"job_pack_id": jid, "step_index": i, "reason": reason})
            run.status = "blocked"
            save_run(run, root)
            if stop_on_first_blocked:
                return _run_result(run, message=f"Blocked at step {i}: {reason}")
            continue

        job = get_job_pack(jid, root)
        if not job:
            run.blocked.append({"job_pack_id": jid, "step_index": i, "reason": "job not found"})
            run.status = "blocked"
            save_run(run, root)
            if stop_on_first_blocked:
                return _run_result(run)
            continue

        spec = load_specialization(jid, root)
        params = resolve_params(job, spec.preferred_params if spec else {}, {})
        result = run_job(jid, mode, params, root, update_specialization_on_success=False)
        if result.get("error"):
            run.errors.append(f"{jid}: {result['error']}")
            run.blocked.append({"job_pack_id": jid, "step_index": i, "reason": result["error"]})
            run.status = "blocked"
            save_run(run, root)
            if stop_on_first_blocked:
                return _run_result(run)
            continue

        run.executed.append({
            "job_pack_id": jid,
            "step_index": i,
            "outcome": result.get("outcome"),
            "run_id": result.get("run_id"),
        })
        if result.get("artifact_paths"):
            run.artifacts.extend(result.get("artifact_paths", []))

        next_i = i + 1
        should_pause = stop_at_checkpoints and next_i < len(plan.job_pack_ids) and (
            (i in set(checkpoint_after_indices or []))
            or (mode == "real" and classify_step(plan.job_pack_ids[next_i], mode, root).step_type == STEP_TYPE_TRUSTED_REAL)
        )
        if should_pause:
            run.status = "awaiting_approval"
            run.current_step_index = next_i
            run.approval_required_before_step = next_i
            run.timestamp_end = utc_now_iso()
            save_run(run, root)
            save_artifacts_list(run_id, run.artifacts, root)
            return _run_result(
                run,
                message=f"Paused at checkpoint before step {next_i}. Resume: workflow-dataset executor resume --run {run_id}",
            )
        save_run(run, root)

    run = load_run(run_id, root)
    if run:
        run.status = "completed"
        run.current_step_index = len(plan.job_pack_ids)
        run.timestamp_end = utc_now_iso()
        save_run(run, root)
        save_artifacts_list(run_id, run.artifacts, root)
    return _run_result(run or ExecutionRun(run_id=run_id, plan_id=plan.plan_id, status="completed"))


def resume_run(
    run_id: str,
    decision: str = "proceed",
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Resume a run that is awaiting_approval. decision: proceed | cancel | defer.
    On proceed: continue from approval_required_before_step. On cancel: set status cancelled.
    """
    root = Path(repo_root).resolve() if repo_root else None
    run = load_run(run_id, root)
    if not run:
        return {"error": f"Run not found: {run_id}"}
    if run.status != "awaiting_approval":
        return {"error": f"Run not awaiting approval (status={run.status})", "run_id": run_id}

    from workflow_dataset.executor.hub import record_checkpoint_decision
    record_checkpoint_decision(run_id, run.approval_required_before_step or run.current_step_index, decision, root, note="resume")

    if decision == "cancel":
        run.status = "cancelled"
        run.timestamp_end = utc_now_iso()
        save_run(run, root)
        return _run_result(run, message="Run cancelled at checkpoint.")

    if decision != "proceed":
        return _run_result(run, message=f"Decision '{decision}' recorded; use 'proceed' to continue.")

    run.status = "running"
    run.approval_required_before_step = None
    save_run(run, root)

    plan = resolve_plan(run.plan_source, run.plan_ref, run.mode, root)
    if not plan:
        return {"error": "Plan could not be re-resolved for resume", "run_id": run_id}

    start_i = run.current_step_index
    checkpoint_after: set[int] = set()
    for e in run.envelopes:
        if e.checkpoint_required and e.step_index > 0:
            checkpoint_after.add(e.step_index - 1)

    for i in range(start_i, len(plan.job_pack_ids)):
        jid = plan.job_pack_ids[i]
        run = load_run(run_id, root)
        if not run or run.status in ("cancelled", "completed"):
            return _run_result(run or ExecutionRun(run_id=run_id, status="cancelled"))

        run.current_step_index = i
        if jid in plan.blocked:
            reason = plan.blocked_reasons.get(jid, "blocked")
            run.blocked.append({"job_pack_id": jid, "step_index": i, "reason": reason})
            run.status = "blocked"
            save_run(run, root)
            return _run_result(run)
        job = get_job_pack(jid, root)
        if not job:
            run.blocked.append({"job_pack_id": jid, "step_index": i, "reason": "job not found"})
            run.status = "blocked"
            save_run(run, root)
            return _run_result(run)
        spec = load_specialization(jid, root)
        params = resolve_params(job, spec.preferred_params if spec else {}, {})
        result = run_job(jid, run.mode, params, root, update_specialization_on_success=False)
        if result.get("error"):
            run.errors.append(f"{jid}: {result['error']}")
            run.blocked.append({"job_pack_id": jid, "step_index": i, "reason": result["error"]})
            run.status = "blocked"
            save_run(run, root)
            return _run_result(run)
        run.executed.append({
            "job_pack_id": jid,
            "step_index": i,
            "outcome": result.get("outcome"),
            "run_id": result.get("run_id"),
        })
        if result.get("artifact_paths"):
            run.artifacts.extend(result.get("artifact_paths", []))
        next_i = i + 1
        should_pause = next_i < len(plan.job_pack_ids) and (
            (i in checkpoint_after)
            or (run.mode == "real" and classify_step(plan.job_pack_ids[next_i], run.mode, root).step_type == STEP_TYPE_TRUSTED_REAL)
        )
        if should_pause:
            run.status = "awaiting_approval"
            run.current_step_index = next_i
            run.approval_required_before_step = next_i
            run.timestamp_end = utc_now_iso()
            save_run(run, root)
            save_artifacts_list(run_id, run.artifacts, root)
            return _run_result(
                run,
                message=f"Paused at checkpoint before step {next_i}. Resume: workflow-dataset executor resume --run {run_id}",
            )
        save_run(run, root)

    run = load_run(run_id, root)
    if run:
        run.status = "completed"
        run.current_step_index = len(plan.job_pack_ids)
        run.timestamp_end = utc_now_iso()
        save_run(run, root)
        save_artifacts_list(run_id, run.artifacts, root)
    return _run_result(run or ExecutionRun(run_id=run_id, plan_id=plan.plan_id, status="completed"))


def _run_bundle_steps(
    bundle_id: str,
    mode: str,
    repo_root: Path | str | None,
) -> dict[str, Any]:
    """M26H.1: Run all steps in a bundle. Returns {executed: [...], artifacts: [...], error: optional}."""
    root = Path(repo_root).resolve() if repo_root else None
    from workflow_dataset.executor.bundles import get_bundle
    bundle = get_bundle(bundle_id, repo_root)
    if not bundle:
        return {"error": f"Bundle not found: {bundle_id}", "executed": [], "artifacts": []}
    executed: list[dict[str, Any]] = []
    artifacts: list[str] = []
    for step in bundle.steps:
        if step.action_type == "job_run":
            job = get_job_pack(step.action_ref, root)
            if not job:
                return {"error": f"Job not found: {step.action_ref}", "executed": executed, "artifacts": artifacts}
            spec = load_specialization(step.action_ref, root)
            params = resolve_params(job, spec.preferred_params if spec else {}, {})
            result = run_job(step.action_ref, mode, params, root, update_specialization_on_success=False)
            if result.get("error"):
                return {"error": result["error"], "executed": executed, "artifacts": artifacts}
            executed.append({"job_pack_id": step.action_ref, "outcome": result.get("outcome"), "run_id": result.get("run_id")})
            if result.get("artifact_paths"):
                artifacts.extend(result.get("artifact_paths", []))
        elif step.action_type == "adapter_action":
            part = step.action_ref.split(":", 1)
            if len(part) != 2:
                return {"error": f"Invalid adapter_action ref: {step.action_ref}", "executed": executed, "artifacts": artifacts}
            adapter_id, action_id = part[0], part[1]
            from workflow_dataset.desktop_adapters.execute import run_execute
            res = run_execute(adapter_id, action_id, {}, root)
            if not res.success:
                return {"error": res.message, "executed": executed, "artifacts": artifacts}
            executed.append({"adapter_id": adapter_id, "action_id": action_id, "outcome": "ok"})
    return {"executed": executed, "artifacts": artifacts}


def resume_from_blocked(
    run_id: str,
    decision: str,
    repo_root: Path | str | None = None,
    substitute_bundle_id: str = "",
    substitute_action_ref: str = "",
    note: str = "",
) -> dict[str, Any]:
    """
    M26H.1: Human-in-the-loop recovery from blocked run. decision: retry | skip | substitute.
    Records recovery decision; then retries current step, skips it, or runs substitute bundle/action.
    Artifacts from before block are preserved; new artifacts from retry/substitute are merged.
    """
    root = Path(repo_root).resolve() if repo_root else None
    run = load_run(run_id, root)
    if not run:
        return {"error": f"Run not found: {run_id}"}
    if run.status != "blocked":
        return {"error": f"Run is not blocked (status={run.status})", "run_id": run_id}

    step_index = run.current_step_index
    record_recovery_decision(
        run_id, step_index, decision, root,
        substitute_bundle_id=substitute_bundle_id,
        substitute_action_ref=substitute_action_ref,
        note=note,
    )
    run = load_run(run_id, root)
    if not run:
        return {"error": "Run state lost after recording recovery"}

    plan = resolve_plan(run.plan_source, run.plan_ref, run.mode, root)
    if not plan:
        return {"error": "Plan could not be re-resolved for recovery", "run_id": run_id}

    # Preserve existing artifacts (handoff from before block)
    artifacts_before = list(run.artifacts)
    run.status = "running"
    save_run(run, root)

    if decision == "skip":
        run.current_step_index = step_index + 1
        run.executed.append({"step_index": step_index, "recovery": "skip", "note": note})
        save_run(run, root)
        # Continue from next step
        return _continue_run_after_recovery(run_id, step_index + 1, plan, run.mode, root, artifacts_before)

    if decision == "retry":
        jid = plan.job_pack_ids[step_index] if step_index < len(plan.job_pack_ids) else ""
        if not jid:
            return {"error": "No job at step_index for retry", "run_id": run_id}
        job = get_job_pack(jid, root)
        if not job:
            run.blocked.append({"job_pack_id": jid, "step_index": step_index, "reason": "job not found"})
            run.status = "blocked"
            save_run(run, root)
            return _run_result(run)
        spec = load_specialization(jid, root)
        params = resolve_params(job, spec.preferred_params if spec else {}, {})
        result = run_job(jid, run.mode, params, root, update_specialization_on_success=False)
        if result.get("error"):
            run.errors.append(f"{jid}: {result['error']}")
            run.blocked.append({"job_pack_id": jid, "step_index": step_index, "reason": result["error"]})
            run.status = "blocked"
            save_run(run, root)
            return _run_result(run, message="Retry failed again.")
        run.executed.append({"job_pack_id": jid, "step_index": step_index, "outcome": result.get("outcome"), "run_id": result.get("run_id"), "recovery": "retry"})
        if result.get("artifact_paths"):
            run.artifacts.extend(result.get("artifact_paths", []))
        save_artifacts_list(run_id, run.artifacts, root)
        save_run(run, root)
        return _continue_run_after_recovery(run_id, step_index + 1, plan, run.mode, root, list(run.artifacts))

    if decision == "substitute":
        if substitute_bundle_id:
            out = _run_bundle_steps(substitute_bundle_id, run.mode, root)
            if out.get("error"):
                run.status = "blocked"
                run.errors.append(out["error"])
                run.blocked.append({"step_index": step_index, "reason": out["error"], "recovery": "substitute"})
                save_run(run, root)
                return _run_result(run)
            run.executed.extend([{"step_index": step_index, "recovery": "substitute", **e} for e in out["executed"]])
            run.artifacts = artifacts_before + out.get("artifacts", [])
            save_artifacts_list(run_id, run.artifacts, root)
            save_run(run, root)
            return _continue_run_after_recovery(run_id, step_index + 1, plan, run.mode, root, list(run.artifacts))
        if substitute_action_ref:
            if ":" in substitute_action_ref:
                adapter_id, action_id = substitute_action_ref.split(":", 1)
                from workflow_dataset.desktop_adapters.execute import run_execute
                res = run_execute(adapter_id, action_id, {}, root)
                if not res.success:
                    run.status = "blocked"
                    run.errors.append(res.message)
                    run.blocked.append({"step_index": step_index, "reason": res.message, "recovery": "substitute"})
                    save_run(run, root)
                    return _run_result(run)
                run.executed.append({"step_index": step_index, "recovery": "substitute", "adapter_id": adapter_id, "action_id": action_id})
                run.artifacts = list(artifacts_before)
            else:
                job = get_job_pack(substitute_action_ref, root)
                if not job:
                    run.status = "blocked"
                    run.blocked.append({"step_index": step_index, "reason": "substitute job not found", "recovery": "substitute"})
                    save_run(run, root)
                    return _run_result(run)
                spec = load_specialization(substitute_action_ref, root)
                params = resolve_params(job, spec.preferred_params if spec else {}, {})
                result = run_job(substitute_action_ref, run.mode, params, root, update_specialization_on_success=False)
                if result.get("error"):
                    run.status = "blocked"
                    run.errors.append(result["error"])
                    save_run(run, root)
                    return _run_result(run)
                run.executed.append({"job_pack_id": substitute_action_ref, "step_index": step_index, "recovery": "substitute", "outcome": result.get("outcome")})
                if result.get("artifact_paths"):
                    run.artifacts = artifacts_before + result.get("artifact_paths", [])
                    save_artifacts_list(run_id, run.artifacts, root)
            save_run(run, root)
            return _continue_run_after_recovery(run_id, step_index + 1, plan, run.mode, root, list(run.artifacts))
        return {"error": "substitute requires --substitute-bundle or --substitute-action-ref", "run_id": run_id}

    return {"error": f"Unknown decision: {decision}", "run_id": run_id}


def _continue_run_after_recovery(
    run_id: str,
    start_i: int,
    plan: Any,
    mode: str,
    root: Path | None,
    artifacts_so_far: list[str],
) -> dict[str, Any]:
    """Continue plan execution from start_i; merge artifacts_so_far into run.artifacts."""
    from workflow_dataset.copilot.plan import PlanPreview
    run = load_run(run_id, root)
    if not run:
        return {"error": "Run state lost"}
    run.artifacts = list(artifacts_so_far)
    checkpoint_after: set[int] = set()
    for e in run.envelopes:
        if e.checkpoint_required and e.step_index > 0:
            checkpoint_after.add(e.step_index - 1)
    for i in range(start_i, len(plan.job_pack_ids)):
        jid = plan.job_pack_ids[i]
        run = load_run(run_id, root)
        if not run or run.status in ("cancelled", "completed"):
            return _run_result(run or ExecutionRun(run_id=run_id, status="cancelled"))
        run.current_step_index = i
        if jid in plan.blocked:
            reason = plan.blocked_reasons.get(jid, "blocked")
            run.blocked.append({"job_pack_id": jid, "step_index": i, "reason": reason})
            run.status = "blocked"
            save_run(run, root)
            save_artifacts_list(run_id, run.artifacts, root)
            return _run_result(run)
        job = get_job_pack(jid, root)
        if not job:
            run.blocked.append({"job_pack_id": jid, "step_index": i, "reason": "job not found"})
            run.status = "blocked"
            save_run(run, root)
            save_artifacts_list(run_id, run.artifacts, root)
            return _run_result(run)
        spec = load_specialization(jid, root)
        params = resolve_params(job, spec.preferred_params if spec else {}, {})
        result = run_job(jid, mode, params, root, update_specialization_on_success=False)
        if result.get("error"):
            run.errors.append(f"{jid}: {result['error']}")
            run.blocked.append({"job_pack_id": jid, "step_index": i, "reason": result["error"]})
            run.status = "blocked"
            save_run(run, root)
            save_artifacts_list(run_id, run.artifacts, root)
            return _run_result(run)
        run.executed.append({"job_pack_id": jid, "step_index": i, "outcome": result.get("outcome"), "run_id": result.get("run_id")})
        if result.get("artifact_paths"):
            run.artifacts.extend(result.get("artifact_paths", []))
        next_i = i + 1
        should_pause = next_i < len(plan.job_pack_ids) and (
            (i in checkpoint_after)
            or (mode == "real" and classify_step(plan.job_pack_ids[next_i], mode, root).step_type == STEP_TYPE_TRUSTED_REAL)
        )
        if should_pause:
            run.status = "awaiting_approval"
            run.current_step_index = next_i
            run.approval_required_before_step = next_i
            run.timestamp_end = utc_now_iso()
            save_run(run, root)
            save_artifacts_list(run_id, run.artifacts, root)
            return _run_result(run, message=f"Paused at checkpoint before step {next_i}. Resume: workflow-dataset executor resume --run {run_id}")
        save_run(run, root)
        save_artifacts_list(run_id, run.artifacts, root)

    run = load_run(run_id, root)
    if run:
        run.status = "completed"
        run.current_step_index = len(plan.job_pack_ids)
        run.timestamp_end = utc_now_iso()
        save_run(run, root)
        save_artifacts_list(run_id, run.artifacts, root)
    return _run_result(run or ExecutionRun(run_id=run_id, plan_id=plan.plan_id, status="completed"))


def _run_result(run: ExecutionRun, message: str = "") -> dict[str, Any]:
    out = {
        "run_id": run.run_id,
        "plan_id": run.plan_id,
        "plan_ref": run.plan_ref,
        "mode": run.mode,
        "status": run.status,
        "current_step_index": run.current_step_index,
        "executed_count": len(run.executed),
        "blocked_count": len(run.blocked),
        "artifacts_count": len(run.artifacts),
        "run_path": run.run_path,
        "timestamp_start": run.timestamp_start,
        "timestamp_end": run.timestamp_end,
    }
    if message:
        out["message"] = message
    if run.errors:
        out["errors"] = run.errors
    return out

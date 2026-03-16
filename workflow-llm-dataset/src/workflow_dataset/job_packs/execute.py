"""
M23J: Parameterized job execution. Resolve params, preview, run via task or benchmark.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.job_packs.schema import JobPack, get_job_pack
from workflow_dataset.job_packs.specialization import load_specialization
from workflow_dataset.job_packs.policy import check_job_policy
from workflow_dataset.task_demos.replay import replay_task_simulate
from workflow_dataset.desktop_bench import run_benchmark
from workflow_dataset.job_packs.specialization import update_from_successful_run


def resolve_params(
    job: JobPack,
    specialization_preferred: dict[str, Any],
    cli_params: dict[str, Any],
) -> dict[str, Any]:
    """
    Resolve final params: schema defaults, then specialization preferred, then CLI override.
    Only include keys that appear in parameter_schema or are used by source steps.
    """
    out: dict[str, Any] = {}
    schema = job.parameter_schema or {}
    for name, spec in schema.items():
        if isinstance(spec, dict) and "default" in spec:
            out[name] = spec["default"]
        elif isinstance(spec, dict):
            out[name] = None
    for k, v in specialization_preferred.items():
        if v is not None:
            out[k] = v
    for k, v in cli_params.items():
        if v is not None and v != "":
            out[k] = v
    return out


def preview_job(
    job_pack_id: str,
    mode: str,
    params: dict[str, Any],
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """Preview resolved params and policy result; no execution."""
    root = Path(repo_root).resolve() if repo_root else None
    job = get_job_pack(job_pack_id, root)
    if not job:
        return {"error": f"Job pack not found: {job_pack_id}"}
    spec = load_specialization(job_pack_id, root)
    resolved = resolve_params(job, spec.preferred_params, params)
    allowed, msg = check_job_policy(job, mode, resolved, root)
    return {
        "job_pack_id": job_pack_id,
        "mode": mode,
        "resolved_params": resolved,
        "policy_allowed": allowed,
        "policy_message": msg,
        "source": _source_to_dict(job.source) if job.source else {},
    }


def _source_to_dict(source: Any) -> dict:
    if hasattr(source, "kind") and hasattr(source, "ref"):
        return {"kind": source.kind, "ref": source.ref}
    return {}


def run_job(
    job_pack_id: str,
    mode: str,
    params: dict[str, Any] | None = None,
    repo_root: Path | str | None = None,
    update_specialization_on_success: bool = False,
) -> dict[str, Any]:
    """
    Run job: resolve params, check policy, execute via task_demo or benchmark, return run result.
    If update_specialization_on_success and outcome is pass, update specialization from this run (explicit path).
    """
    root = Path(repo_root).resolve() if repo_root else None
    params = params or {}
    job = get_job_pack(job_pack_id, root)
    if not job:
        return {"error": f"Job pack not found: {job_pack_id}"}
    spec = load_specialization(job_pack_id, root)
    resolved = resolve_params(job, spec.preferred_params, params)
    allowed, msg = check_job_policy(job, mode, resolved, root)
    if not allowed:
        return {"error": msg, "job_pack_id": job_pack_id}

    source = job.source
    if not source:
        return {"error": f"Job {job_pack_id} has no source (task_demo or benchmark_case).", "job_pack_id": job_pack_id}

    if source.kind == "task_demo":
        if mode == "real":
            return {"error": "Task demo replay is simulate-only.", "job_pack_id": job_pack_id}
        task, results = replay_task_simulate(source.ref, root)
        if not task:
            return {"error": f"Task not found: {source.ref}", "job_pack_id": job_pack_id}
        errors = [r.message for r in results if not r.success]
        outcome = "pass" if not errors else "fail"
        run_id = f"task_{source.ref}_{len(results)}"
        result = {
            "job_pack_id": job_pack_id,
            "mode": "simulate",
            "outcome": outcome,
            "run_id": run_id,
            "source_kind": "task_demo",
            "source_ref": source.ref,
            "resolved_params": resolved,
            "errors": errors,
        }
        if outcome == "pass" and update_specialization_on_success:
            from workflow_dataset.utils.dates import utc_now_iso
            update_from_successful_run(job_pack_id, run_id, utc_now_iso(), resolved, outcome, root)
        return result

    if source.kind == "benchmark_case":
        # Map resolved params into benchmark case step params (e.g. path -> steps[].params.path)
        bench_result = run_benchmark(source.ref, mode, repo_root=root)
        if bench_result.get("error"):
            return {"error": bench_result["error"], "job_pack_id": job_pack_id}
        outcome = bench_result.get("outcome", "fail")
        run_id = bench_result.get("run_id", "")
        result = {
            "job_pack_id": job_pack_id,
            "mode": mode,
            "outcome": outcome,
            "run_id": run_id,
            "run_path": bench_result.get("run_path"),
            "source_kind": "benchmark_case",
            "source_ref": source.ref,
            "resolved_params": resolved,
            "errors": bench_result.get("errors", []),
        }
        if outcome == "pass" and update_specialization_on_success:
            from workflow_dataset.utils.dates import utc_now_iso
            update_from_successful_run(job_pack_id, run_id, utc_now_iso(), resolved, outcome, root)
        return result

    return {"error": f"Unsupported source kind: {source.kind}", "job_pack_id": job_pack_id}

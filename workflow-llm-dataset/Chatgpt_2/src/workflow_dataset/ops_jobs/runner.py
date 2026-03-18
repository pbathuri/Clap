"""
M41I–M41L: Run one ops job — dispatch to existing APIs, persist output and history.
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
        return prefix + hashlib.sha256("".join(str(p) for p in parts).encode()).hexdigest()[:12]

from workflow_dataset.ops_jobs.models import JobOutput
from workflow_dataset.ops_jobs.registry import get_ops_job
from workflow_dataset.ops_jobs.store import append_run


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _run_reliability_run(args: list[str], root: Path) -> dict[str, Any]:
    path_id = (args or ["golden_first_run"])[0]
    try:
        from workflow_dataset.reliability.harness import run_golden_path
        from workflow_dataset.reliability.store import save_run
        result = run_golden_path(path_id, repo_root=root)
        save_run(result, repo_root=root)
        outcome = "pass" if result.outcome in ("pass", "degraded") else "fail"
        return {
            "outcome": outcome,
            "summary": f"{result.path_name}: {result.outcome}",
            "output_refs": {"reliability_run_id": getattr(result, "run_id", ""), "path_id": path_id},
            "linked_surfaces": ["reliability"],
        }
    except Exception as e:
        return {"outcome": "fail", "summary": str(e), "error_message": str(e), "output_refs": {}, "linked_surfaces": ["reliability"]}


def _run_triage_health(root: Path) -> dict[str, Any]:
    try:
        from workflow_dataset.triage.health import build_cohort_health_summary
        h = build_cohort_health_summary(repo_root=root)
        outcome = "pass" if h.get("open_issue_count", 0) == 0 or h.get("highest_severity") not in ("critical",) else "degraded"
        return {
            "outcome": outcome,
            "summary": f"open_issues={h.get('open_issue_count')} severity={h.get('highest_severity')}",
            "output_refs": {},
            "linked_surfaces": ["triage", "cohort"],
        }
    except Exception as e:
        return {"outcome": "fail", "summary": str(e), "error_message": str(e), "output_refs": {}, "linked_surfaces": ["triage"]}


def _run_deploy_bundle_validate(root: Path) -> dict[str, Any]:
    try:
        from workflow_dataset.deploy_bundle import validate_bundle, get_active_bundle
        active = get_active_bundle(repo_root=root)
        bundle_id = active.get("active_bundle_id", "") or "founder_operator_prod"
        result = validate_bundle(bundle_id, repo_root=root)
        outcome = "pass" if result.passed else "fail"
        return {
            "outcome": outcome,
            "summary": f"validation passed={result.passed} errors={len(result.errors)}",
            "output_refs": {"bundle_id": bundle_id},
            "linked_surfaces": ["deploy_bundle"],
            "blocked_reason": "; ".join(result.errors[:2]) if result.errors else "",
        }
    except Exception as e:
        return {"outcome": "fail", "summary": str(e), "error_message": str(e), "output_refs": {}, "linked_surfaces": ["deploy_bundle"]}


def _run_vertical_packs_progress(root: Path) -> dict[str, Any]:
    try:
        from workflow_dataset.vertical_packs import build_milestone_progress_output
        out = build_milestone_progress_output(repo_root=root)
        outcome = "pass"
        return {
            "outcome": outcome,
            "summary": f"active_pack={out.get('active_curated_pack_id') or '(none)'} next_milestone={out.get('next_milestone_id') or '—'}",
            "output_refs": {},
            "linked_surfaces": ["vertical_packs"],
        }
    except Exception as e:
        return {"outcome": "fail", "summary": str(e), "error_message": str(e), "output_refs": {}, "linked_surfaces": ["vertical_packs"]}


def _run_release_readiness(root: Path) -> dict[str, Any]:
    try:
        from workflow_dataset.release_readiness.readiness import build_release_readiness
        r = build_release_readiness(repo_root=root)
        outcome = "pass" if r.status == "ready" else "degraded"
        return {
            "outcome": outcome,
            "summary": f"readiness={r.status} blockers={len(r.blockers)}",
            "output_refs": {},
            "linked_surfaces": ["release_readiness", "support"],
        }
    except Exception as e:
        return {"outcome": "fail", "summary": str(e), "error_message": str(e), "output_refs": {}, "linked_surfaces": ["release_readiness"]}


def _run_maintenance_mode_report(root: Path) -> dict[str, Any]:
    try:
        from workflow_dataset.deploy_bundle import build_maintenance_mode_report
        r = build_maintenance_mode_report(repo_root=root)
        outcome = "pass"
        return {
            "outcome": outcome,
            "summary": f"profile={r.active_profile_id} mode={r.active_maintenance_mode_id or '(none)'} should_repair={r.should_repair}",
            "output_refs": {},
            "linked_surfaces": ["deploy_bundle"],
        }
    except Exception as e:
        return {"outcome": "fail", "summary": str(e), "error_message": str(e), "output_refs": {}, "linked_surfaces": ["deploy_bundle"]}


def _run_queue_summary(root: Path) -> dict[str, Any]:
    try:
        from workflow_dataset.unified_queue.collect import build_unified_queue
        from workflow_dataset.unified_queue.summary import build_queue_summary
        items = build_unified_queue(repo_root=root, limit=50)
        s = build_queue_summary(items)
        outcome = "pass"
        total = getattr(s, "total_count", len(items))
        return {
            "outcome": outcome,
            "summary": f"queue total={total}",
            "output_refs": {},
            "linked_surfaces": ["queue"],
        }
    except Exception as e:
        return {"outcome": "fail", "summary": str(e), "error_message": str(e), "output_refs": {}, "linked_surfaces": ["queue"]}


def _run_devlab_queue(root: Path) -> dict[str, Any]:
    try:
        from workflow_dataset.devlab.experiments import get_queue_status
        eq = get_queue_status(root / "data/local/devlab")
        outcome = "pass"
        return {
            "outcome": outcome,
            "summary": f"queued={eq.get('queued', 0)} running={eq.get('running', 0)}",
            "output_refs": {},
            "linked_surfaces": ["development"],
        }
    except Exception as e:
        return {"outcome": "fail", "summary": str(e), "error_message": str(e), "output_refs": {}, "linked_surfaces": ["development"]}


def run_ops_job(job_id: str, repo_root: Path | str | None = None) -> JobOutput:
    """Run one ops job; dispatch by run_command; persist to history. Returns JobOutput."""
    root = _repo_root(repo_root)
    job = get_ops_job(job_id)
    if not job:
        out = JobOutput(
            run_id=stable_id("ops", job_id, utc_now_iso(), prefix="run_"),
            job_id=job_id,
            outcome="blocked",
            summary=f"Unknown job: {job_id}",
            started_utc=utc_now_iso(),
            finished_utc=utc_now_iso(),
            error_message=f"Job not found: {job_id}",
        )
        return out

    started = utc_now_iso()
    run_id = stable_id("ops", job_id, started, prefix="run_")

    # Optional prerequisite: for reliability_refresh, check install
    if job_id == "reliability_refresh" and job.prerequisites:
        try:
            from workflow_dataset.local_deployment.install_check import run_install_check
            check = run_install_check(repo_root=root)
            if not check.get("passed", False):
                finished = utc_now_iso()
                out = JobOutput(
                    run_id=run_id,
                    job_id=job_id,
                    outcome="blocked",
                    summary="Prerequisite failed: install check",
                    started_utc=started,
                    finished_utc=finished,
                    blocked_reason="Install check failed",
                    output_refs={},
                    linked_surfaces=job.output_surfaces,
                )
                append_run(job_id, out.to_dict(), repo_root=root)
                return out
        except Exception:
            pass

    dispatch = {
        "reliability_run": _run_reliability_run,
        "queue_summary": lambda args, r: _run_queue_summary(r),
        "triage_health": lambda args, r: _run_triage_health(r),
        "devlab_queue": lambda args, r: _run_devlab_queue(r),
        "deploy_bundle_validate": lambda args, r: _run_deploy_bundle_validate(r),
        "vertical_packs_progress": lambda args, r: _run_vertical_packs_progress(r),
        "release_readiness": lambda args, r: _run_release_readiness(r),
        "maintenance_mode_report": lambda args, r: _run_maintenance_mode_report(r),
    }
    fn = dispatch.get(job.run_command)
    if not fn:
        finished = utc_now_iso()
        out = JobOutput(
            run_id=run_id,
            job_id=job_id,
            outcome="blocked",
            summary=f"No runner for run_command={job.run_command}",
            started_utc=started,
            finished_utc=finished,
            error_message=f"Unknown run_command: {job.run_command}",
            output_refs={},
            linked_surfaces=job.output_surfaces,
        )
        append_run(job_id, out.to_dict(), repo_root=root)
        return out

    try:
        import time
        t0 = time.monotonic()
        result = fn(job.run_command_args, root)
        duration = time.monotonic() - t0
        finished = utc_now_iso()
        out = JobOutput(
            run_id=run_id,
            job_id=job_id,
            outcome=result.get("outcome", "pass"),
            summary=result.get("summary", ""),
            started_utc=started,
            finished_utc=finished,
            duration_seconds=round(duration, 2),
            output_refs=result.get("output_refs", {}),
            linked_surfaces=result.get("linked_surfaces", job.output_surfaces),
            blocked_reason=result.get("blocked_reason", ""),
            error_message=result.get("error_message", ""),
        )
    except Exception as e:
        finished = utc_now_iso()
        out = JobOutput(
            run_id=run_id,
            job_id=job_id,
            outcome="fail",
            summary=str(e),
            started_utc=started,
            finished_utc=finished,
            error_message=str(e),
            output_refs={},
            linked_surfaces=job.output_surfaces,
        )
    append_run(job_id, out.to_dict(), repo_root=root)
    return out

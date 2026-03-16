"""
M23K: Operator-approved plan execution. Record plan run; stop on blocked unless override.
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

from workflow_dataset.copilot.plan import build_plan_for_job, build_plan_for_routine, PlanPreview
from workflow_dataset.job_packs import run_job, get_job_pack, load_specialization
from workflow_dataset.job_packs.execute import resolve_params
from workflow_dataset.copilot.config import get_runs_dir


def run_plan(
    plan: PlanPreview,
    repo_root: Path | str | None = None,
    stop_on_first_blocked: bool = True,
    continue_on_blocked: bool = False,
) -> dict[str, Any]:
    """
    Execute plan: run each job in order. If stop_on_first_blocked and a step is blocked, stop and record.
    Persist plan run record under data/local/copilot/runs/<run_id>/plan_run.json.
    """
    root = Path(repo_root).resolve() if repo_root else None
    runs_dir = get_runs_dir(root)
    run_id = stable_id("cprun", plan.plan_id, utc_now_iso(), prefix="")[:20]
    run_path = runs_dir / run_id
    run_path.mkdir(parents=True, exist_ok=True)

    executed: list[dict[str, Any]] = []
    blocked_steps: list[dict[str, Any]] = []
    errors: list[str] = []
    approvals_checked: list[dict] = []

    for jid in plan.job_pack_ids:
        if jid in plan.blocked:
            blocked_steps.append({
                "job_pack_id": jid,
                "reason": plan.blocked_reasons.get(jid, "blocked"),
            })
            if stop_on_first_blocked and not continue_on_blocked:
                break
            continue
        job = get_job_pack(jid, root)
        if not job:
            blocked_steps.append({"job_pack_id": jid, "reason": "job not found"})
            if stop_on_first_blocked and not continue_on_blocked:
                break
            continue
        spec = load_specialization(jid, root)
        params = resolve_params(job, spec.preferred_params if spec else {}, {})
        result = run_job(jid, plan.mode, params, root, update_specialization_on_success=False)
        if result.get("error"):
            errors.append(f"{jid}: {result['error']}")
            blocked_steps.append({"job_pack_id": jid, "reason": result["error"]})
            if stop_on_first_blocked and not continue_on_blocked:
                break
            continue
        executed.append({
            "job_pack_id": jid,
            "outcome": result.get("outcome"),
            "run_id": result.get("run_id"),
        })
        if result.get("approvals_checked"):
            approvals_checked.append(result["approvals_checked"])

    record = {
        "plan_run_id": run_id,
        "plan_id": plan.plan_id,
        "job_pack_ids": plan.job_pack_ids,
        "mode": plan.mode,
        "timestamp": utc_now_iso(),
        "approvals_checked": approvals_checked,
        "executed": executed,
        "blocked": blocked_steps,
        "errors": errors,
        "run_path": str(run_path),
    }
    (run_path / "plan_run.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    return {
        "plan_run_id": run_id,
        "run_path": str(run_path),
        "plan_id": plan.plan_id,
        "mode": plan.mode,
        "executed_count": len(executed),
        "blocked_count": len(blocked_steps),
        "errors": errors,
    }


def list_plan_runs(limit: int = 20, repo_root: Path | str | None = None) -> list[dict[str, Any]]:
    """List recent plan run records."""
    runs_dir = get_runs_dir(repo_root)
    if not runs_dir.exists():
        return []
    out = []
    for d in sorted(runs_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
        if d.is_dir():
            f = d / "plan_run.json"
            if f.exists():
                try:
                    data = json.loads(f.read_text(encoding="utf-8"))
                    data["run_path"] = str(d)
                    out.append(data)
                except Exception:
                    pass
        if len(out) >= limit:
            break
    return out

"""
M26E–M26H: Execution run hub — persist runs, artifacts, checkpoint decisions under data/local/executor.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.executor.models import ExecutionRun, BlockedStepRecovery

EXECUTOR_ROOT = "data/local/executor"
RUNS_SUBDIR = "runs"
RUN_STATE_FILE = "run_state.json"
ARTIFACTS_FILE = "artifacts.json"


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def get_executor_runs_dir(repo_root: Path | str | None = None) -> Path:
    """Return data/local/executor/runs; ensure it exists."""
    root = _repo_root(repo_root)
    path = root / EXECUTOR_ROOT / RUNS_SUBDIR
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_run(run: ExecutionRun, repo_root: Path | str | None = None) -> Path:
    """Persist ExecutionRun to runs/<run_id>/run_state.json."""
    root = get_executor_runs_dir(repo_root)
    run_dir = root / run.run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    run.run_path = str(run_dir)
    path = run_dir / RUN_STATE_FILE
    path.write_text(json.dumps(run.to_dict(), indent=2), encoding="utf-8")
    return path


def load_run(run_id: str, repo_root: Path | str | None = None) -> ExecutionRun | None:
    """Load ExecutionRun by run_id."""
    root = get_executor_runs_dir(repo_root)
    path = root / run_id / RUN_STATE_FILE
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return ExecutionRun.from_dict(data)
    except Exception:
        return None


def list_runs(limit: int = 50, repo_root: Path | str | None = None) -> list[dict[str, Any]]:
    """List recent runs (newest first). Returns list of minimal dicts: run_id, status, plan_id, mode, timestamp_start."""
    root = get_executor_runs_dir(repo_root)
    if not root.exists():
        return []
    out: list[dict[str, Any]] = []
    for d in sorted(root.iterdir(), key=lambda x: x.stat().st_mtime if x.is_dir() else 0, reverse=True):
        if not d.is_dir():
            continue
        f = d / RUN_STATE_FILE
        if not f.exists():
            continue
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            out.append({
                "run_id": data.get("run_id", d.name),
                "status": data.get("status", ""),
                "plan_id": data.get("plan_id", ""),
                "plan_ref": data.get("plan_ref", ""),
                "mode": data.get("mode", ""),
                "timestamp_start": data.get("timestamp_start", ""),
                "current_step_index": data.get("current_step_index", 0),
            })
            if len(out) >= limit:
                break
        except Exception:
            continue
    return out


def save_artifacts_list(run_id: str, artifacts: list[str], repo_root: Path | str | None = None) -> Path:
    """Write artifacts list to runs/<run_id>/artifacts.json."""
    root = get_executor_runs_dir(repo_root)
    run_dir = root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_dir / ARTIFACTS_FILE
    path.write_text(json.dumps({"artifacts": artifacts}, indent=2), encoding="utf-8")
    return path


def load_artifacts_list(run_id: str, repo_root: Path | str | None = None) -> list[str]:
    """Load artifacts list for a run."""
    root = get_executor_runs_dir(repo_root)
    path = root / run_id / ARTIFACTS_FILE
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return list(data.get("artifacts", []))
    except Exception:
        return []


def record_checkpoint_decision(
    run_id: str,
    step_index: int,
    decision: str,
    repo_root: Path | str | None = None,
    note: str = "",
) -> bool:
    """Append a checkpoint decision to the run. Returns True if run exists and was updated."""
    run = load_run(run_id, repo_root)
    if not run:
        return False
    try:
        from workflow_dataset.utils.dates import utc_now_iso
    except Exception:
        from datetime import datetime, timezone
        def utc_now_iso() -> str:
            return datetime.now(timezone.utc).isoformat()
    from workflow_dataset.executor.models import CheckpointDecision
    run.checkpoint_decisions.append(CheckpointDecision(
        run_id=run_id,
        step_index=step_index,
        decision=decision,
        timestamp=utc_now_iso(),
        note=note,
    ))
    save_run(run, repo_root)
    return True


def get_recovery_options(
    run_id: str,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    M26H.1: Return recovery options for a blocked run: retry, skip, substitute.
    Includes suggested_bundles from executor bundle registry for substitute flow.
    """
    run = load_run(run_id, repo_root)
    if not run:
        return {"error": f"Run not found: {run_id}"}
    if run.status != "blocked":
        return {"error": f"Run is not blocked (status={run.status})", "run_id": run_id}
    step_index = run.current_step_index
    blocked_entry = run.blocked[-1] if run.blocked else {}
    reason = blocked_entry.get("reason", "unknown")
    job_pack_id = blocked_entry.get("job_pack_id", "")
    try:
        from workflow_dataset.executor.bundles import list_bundles
        bundles = list_bundles(repo_root)
        suggested_bundles = [{"bundle_id": b.bundle_id, "title": b.title, "steps_count": len(b.steps)} for b in bundles[:10]]
    except Exception:
        suggested_bundles = []
    return {
        "run_id": run_id,
        "step_index": step_index,
        "blocked_job_pack_id": job_pack_id,
        "blocked_reason": reason,
        "options": ["retry", "skip", "substitute"],
        "suggested_bundles": suggested_bundles,
        "message": "Use: executor resume-from-blocked --run " + run_id + " --decision <retry|skip|substitute> [--substitute-bundle ID] [--note ...]",
    }


def record_recovery_decision(
    run_id: str,
    step_index: int,
    decision: str,
    repo_root: Path | str | None = None,
    substitute_bundle_id: str = "",
    substitute_action_ref: str = "",
    note: str = "",
) -> bool:
    """M26H.1: Append a blocked-step recovery decision to the run. Returns True if run exists and was updated."""
    run = load_run(run_id, repo_root)
    if not run:
        return False
    try:
        from workflow_dataset.utils.dates import utc_now_iso
    except Exception:
        from datetime import datetime, timezone
        def utc_now_iso() -> str:
            return datetime.now(timezone.utc).isoformat()
    run.recovery_decisions.append(BlockedStepRecovery(
        step_index=step_index,
        decision=decision,
        substitute_bundle_id=substitute_bundle_id,
        substitute_action_ref=substitute_action_ref,
        note=note,
        timestamp=utc_now_iso(),
    ))
    save_run(run, repo_root)
    return True

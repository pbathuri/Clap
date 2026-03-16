"""
M23A: Chain runner — execute one chain locally, persist step outputs, stop on failure.
Operator-started only; no auto-apply or hidden calls.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

from workflow_dataset.chain_lab.config import get_chain_lab_root
from workflow_dataset.chain_lab.definition import load_chain, get_step_by_id_or_index
from workflow_dataset.chain_lab.manifest import (
    run_dir_for,
    step_result_dir,
    save_run_manifest,
    load_run_manifest,
)
from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.utils.hashes import stable_id

# Step types we know how to run (CLI subprocess)
STEP_TYPE_CLI = "cli"
STOP_ON_FIRST_FAILURE = "stop_on_first_failure"


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root())
    except Exception:
        return Path.cwd().resolve()


def _run_cli_step(
    step: dict[str, Any],
    run_dir: Path,
    step_index: int,
    repo_root: Path,
    cli_entrypoint: str = "workflow-dataset",
) -> dict[str, Any]:
    """
    Execute one step as CLI. params: { "command": "release", "args": ["demo", "--workflow", "weekly_status", "--save-artifact"] }.
    Returns step result dict: status, started_at, ended_at, output_paths, stdout_path, stderr_path, error.
    """
    params = step.get("params") or {}
    # args: full CLI args e.g. ["release", "demo", "--workflow", "weekly_status", "--save-artifact"]
    raw = params.get("args") or params.get("command")
    if raw is None:
        raw = ["release", "demo", "--workflow", "weekly_status", "--save-artifact"]
    args = [raw] if isinstance(raw, str) else list(raw)
    if args and args[0] != "release":
        args = ["release", "demo"] + args
    cli_cmd = [sys.executable, "-m", "workflow_dataset.cli"]
    full_args = args
    step_dir = step_result_dir(run_dir.name, step_index, repo_root)
    started_at = utc_now_iso()
    stdout_path = step_dir / "stdout.txt"
    stderr_path = step_dir / "stderr.txt"
    input_snapshot_path = step_dir / "input_snapshot.json"
    # Persist input snapshot
    input_snapshot_path.write_text(
        __import__("json").dumps({"step": step, "params": params, "started_at": started_at}, indent=2),
        encoding="utf-8",
    )
    cmd = cli_cmd + full_args
    try:
        with open(stdout_path, "w", encoding="utf-8") as fo, open(stderr_path, "w", encoding="utf-8") as fe:
            result = subprocess.run(
                cmd,
                cwd=str(repo_root),
                timeout=params.get("timeout", 300),
                stdout=fo,
                stderr=fe,
                env=None,
            )
        ended_at = utc_now_iso()
        success = result.returncode == 0
        status = "success" if success else "failed"
        error = None if success else f"exit code {result.returncode}"
    except subprocess.TimeoutExpired:
        ended_at = utc_now_iso()
        status = "failed"
        error = "timeout"
    except Exception as e:
        ended_at = utc_now_iso()
        status = "failed"
        error = str(e)
    # Output paths: step dir contents (excluding input snapshot for "outputs")
    output_paths = [str(stdout_path), str(stderr_path)]
    for f in step_dir.iterdir():
        if f.is_file() and f.name not in ("stdout.txt", "stderr.txt", "input_snapshot.json"):
            output_paths.append(str(f))
    return {
        "step_index": step_index,
        "step_id": step.get("id", ""),
        "label": step.get("label", ""),
        "status": status,
        "started_at": started_at,
        "ended_at": ended_at,
        "output_paths": output_paths,
        "stdout_path": str(stdout_path),
        "stderr_path": str(stderr_path),
        "error": error,
    }


def run_chain(
    chain_id: str,
    variant_label: str | None = None,
    stop_on_first_failure: bool = True,
    repo_root: Path | str | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """
    Run one chain by id. Loads definition, runs each step (CLI subprocess), persists step results.
    Returns run manifest dict (run_id, chain_id, status, step_results, failure_summary).
    """
    root = _repo_root(repo_root)
    definition = load_chain(chain_id, repo_root)
    steps = definition.get("steps") or []
    variant = (variant_label or definition.get("variant_label") or "").strip()
    rid = run_id or stable_id(chain_id, utc_now_iso(), prefix="")[:12]
    run_dir = run_dir_for(rid, repo_root)
    started_at = utc_now_iso()
    step_results: list[dict[str, Any]] = []
    failure_summary: str | None = None
    status = "running"
    for i, step in enumerate(steps):
        step_type = (step.get("type") or STEP_TYPE_CLI).strip() or STEP_TYPE_CLI
        if step_type == STEP_TYPE_CLI:
            res = _run_cli_step(step, run_dir, i, root)
        else:
            res = {
                "step_index": i,
                "step_id": step.get("id", ""),
                "label": step.get("label", ""),
                "status": "skipped",
                "started_at": utc_now_iso(),
                "ended_at": utc_now_iso(),
                "output_paths": [],
                "error": f"unknown step type: {step_type}",
            }
        step_results.append(res)
        if res.get("status") == "failed":
            status = "failed"
            failure_summary = res.get("error") or f"Step {i} ({res.get('step_id', '')}) failed."
            if stop_on_first_failure:
                break
    if status == "running":
        status = "success"
    ended_at = utc_now_iso()
    save_run_manifest(
        run_id=rid,
        chain_id=chain_id,
        variant_label=variant,
        status=status,
        step_results=step_results,
        started_at=started_at,
        ended_at=ended_at,
        failure_summary=failure_summary,
        repo_root=repo_root,
    )
    return load_run_manifest(rid, repo_root) or {}


def resume_chain(
    run_id: str,
    from_step_index: int = 0,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Resume a chain run from a given step index. Loads existing manifest and chain;
    keeps step_results for indices < from_step_index, re-runs steps from_step_index to end.
    Updates manifest with merged results. Safe only when prior steps are already successful.
    """
    root = _repo_root(repo_root)
    manifest = load_run_manifest(run_id, repo_root)
    if not manifest:
        return {"error": "run not found", "run_id": run_id}
    chain_id = manifest.get("chain_id", "")
    if not chain_id:
        return {"error": "manifest missing chain_id", "run_id": run_id}
    definition = load_chain(chain_id, repo_root)
    steps = definition.get("steps") or []
    if from_step_index >= len(steps):
        return manifest
    existing = manifest.get("step_results") or []
    # Keep results for steps before from_step_index
    step_results: list[dict[str, Any]] = list(existing[:from_step_index])
    run_dir = run_dir_for(run_id, repo_root)
    started_at = manifest.get("started_at") or utc_now_iso()
    failure_summary: str | None = None
    status = "running"
    for i in range(from_step_index, len(steps)):
        step = steps[i]
        step_type = (step.get("type") or STEP_TYPE_CLI).strip() or STEP_TYPE_CLI
        if step_type == STEP_TYPE_CLI:
            res = _run_cli_step(step, run_dir, i, root)
        else:
            res = {
                "step_index": i,
                "step_id": step.get("id", ""),
                "label": step.get("label", ""),
                "status": "skipped",
                "started_at": utc_now_iso(),
                "ended_at": utc_now_iso(),
                "output_paths": [],
                "error": f"unknown step type: {step_type}",
            }
        step_results.append(res)
        if res.get("status") == "failed":
            status = "failed"
            failure_summary = res.get("error") or f"Step {i} ({res.get('step_id', '')}) failed."
            break
    if status == "running":
        status = "success"
    ended_at = utc_now_iso()
    save_run_manifest(
        run_id=run_id,
        chain_id=chain_id,
        variant_label=manifest.get("variant_label") or "",
        status=status,
        step_results=step_results,
        started_at=started_at,
        ended_at=ended_at,
        failure_summary=failure_summary,
        repo_root=repo_root,
    )
    return load_run_manifest(run_id, repo_root) or {}


def retry_step(
    run_id: str,
    step_index_or_id: str | int,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Retry a single step of an existing run. Loads manifest and chain, re-runs that step,
    replaces the step result in manifest, recomputes overall status, saves.
    """
    root = _repo_root(repo_root)
    manifest = load_run_manifest(run_id, repo_root)
    if not manifest:
        return {"error": "run not found", "run_id": run_id}
    chain_id = manifest.get("chain_id", "")
    if not chain_id:
        return {"error": "manifest missing chain_id", "run_id": run_id}
    definition = load_chain(chain_id, repo_root)
    step_info = get_step_by_id_or_index(definition, step_index_or_id)
    if not step_info:
        return {"error": f"step not found: {step_index_or_id}", "run_id": run_id}
    step, step_index = step_info
    step_results = list(manifest.get("step_results") or [])
    while len(step_results) <= step_index:
        step_results.append({
            "step_index": len(step_results),
            "step_id": "",
            "label": "",
            "status": "skipped",
            "started_at": "",
            "ended_at": "",
            "output_paths": [],
            "error": "not run",
        })
    run_dir = run_dir_for(run_id, repo_root)
    step_type = (step.get("type") or STEP_TYPE_CLI).strip() or STEP_TYPE_CLI
    if step_type == STEP_TYPE_CLI:
        res = _run_cli_step(step, run_dir, step_index, root)
    else:
        res = {
            "step_index": step_index,
            "step_id": step.get("id", ""),
            "label": step.get("label", ""),
            "status": "skipped",
            "started_at": utc_now_iso(),
            "ended_at": utc_now_iso(),
            "output_paths": [],
            "error": f"unknown step type: {step_type}",
        }
    step_results[step_index] = res
    # Recompute overall status and failure_summary
    status = "success"
    failure_summary: str | None = None
    for r in step_results:
        if r.get("status") == "failed":
            status = "failed"
            failure_summary = r.get("error") or f"Step {r.get('step_index')} ({r.get('step_id', '')}) failed."
            break
    ended_at = utc_now_iso()
    save_run_manifest(
        run_id=run_id,
        chain_id=chain_id,
        variant_label=manifest.get("variant_label") or "",
        status=status,
        step_results=step_results,
        started_at=manifest.get("started_at") or ended_at,
        ended_at=ended_at,
        failure_summary=failure_summary,
        repo_root=repo_root,
    )
    return load_run_manifest(run_id, repo_root) or {}

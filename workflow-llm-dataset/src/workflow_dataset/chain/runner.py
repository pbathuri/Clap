"""
M23A: Chain runner. Execute steps locally, persist outputs, support stop on failure. No auto-apply.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from workflow_dataset.chain.registry import load_chain, _repo_root, _expand_step_to_cmd

RUNS_DIR = "data/local/chains/runs"
DEFAULT_STEP_TIMEOUT = 300


def _runs_path(repo_root: Path | str | None) -> Path:
    return _repo_root(repo_root) / RUNS_DIR


def run_chain(
    chain_id: str,
    repo_root: Path | str | None = None,
    stop_on_failure: bool = True,
    step_timeout: int = DEFAULT_STEP_TIMEOUT,
    operator_notes: str = "",
) -> Path:
    """
    Run a chain: create run dir, execute each step (via subprocess CLI), persist step outputs.
    Returns path to run directory. Raises on chain not found; step failures recorded in run report.
    """
    root = _repo_root(repo_root)
    chain = load_chain(chain_id, repo_root=root)
    stop_conditions = chain.get("stop_conditions") or {}
    stop_on_failure = stop_conditions.get("on_step_failure", stop_on_failure)
    from workflow_dataset.utils.dates import utc_now_iso
    from workflow_dataset.utils.hashes import stable_id
    ts = utc_now_iso()[:19].replace(":", "").replace("-", "")[:14]
    rid = stable_id("chain_run", chain_id, ts, prefix="")[:8]
    run_dir = _runs_path(root) / f"{ts}_{rid}"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "chain_definition.json").write_text(
        json.dumps(chain, indent=2), encoding="utf-8"
    )
    steps_done: list[dict[str, Any]] = []
    final_status = "completed"
    last_step_index = -1
    steps_list = chain.get("steps") or []
    for i, step in enumerate(steps_list):
        step_id = step.get("id") or f"step_{i}"
        cmd = _expand_step_to_cmd(step, root)
        if not cmd:
            step_result = {"step_id": step_id, "status": "skipped", "message": "empty or invalid step command", "exit_code": None}
            steps_done.append(step_result)
            (run_dir / f"step_{i}_{step_id}.json").write_text(json.dumps(step_result, indent=2), encoding="utf-8")
            continue
        log_path = run_dir / f"step_{i}_{step_id}.log"
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                cwd=str(root),
                capture_output=True,
                text=True,
                timeout=step_timeout,
            )
            log_path.write_text(
                f"=== stdout ===\n{result.stdout or ''}\n=== stderr ===\n{result.stderr or ''}",
                encoding="utf-8",
            )
            step_result = {
                "step_id": step_id,
                "status": "ok" if result.returncode == 0 else "failed",
                "exit_code": result.returncode,
                "stdout_path": str(log_path),
                "stderr_path": str(log_path),
            }
            if result.returncode != 0:
                step_result["message"] = result.stderr[:500] if result.stderr else "non-zero exit"
                final_status = "failed"
                last_step_index = i
                if stop_on_failure:
                    break
        except subprocess.TimeoutExpired:
            step_result = {"step_id": step_id, "status": "failed", "message": "timeout", "exit_code": None}
            final_status = "failed"
            last_step_index = i
            if stop_on_failure:
                break
        except Exception as e:
            step_result = {"step_id": step_id, "status": "failed", "message": str(e)[:500], "exit_code": None}
            final_status = "failed"
            last_step_index = i
            if stop_on_failure:
                break
        steps_done.append(step_result)
        (run_dir / f"step_{i}_{step_id}.json").write_text(json.dumps(step_result, indent=2), encoding="utf-8")
    report: dict[str, Any] = {
        "run_id": run_dir.name,
        "run_dir": str(run_dir),
        "chain_id": chain_id,
        "status": final_status,
        "steps": steps_done,
        "steps_total": len(steps_list),
        "last_step_index": last_step_index,
        "expected_artifacts": chain.get("expected_artifacts", []),
        "operator_notes": operator_notes,
    }
    (run_dir / "run_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return run_dir


def get_run_status(run_spec: str, repo_root: Path | str | None = None) -> dict[str, Any] | None:
    """
    Get status for a run. run_spec: run_id (directory name) or "latest".
    Returns run_report.json content plus step files listing.
    """
    root = _repo_root(repo_root)
    runs_base = _runs_path(root)
    if not runs_base.exists():
        return None
    if run_spec.strip().lower() == "latest":
        dirs = sorted([d for d in runs_base.iterdir() if d.is_dir()], key=lambda d: d.name, reverse=True)
        if not dirs:
            return None
        run_dir = dirs[0]
    else:
        run_dir = runs_base / run_spec.strip()
        if not run_dir.exists() or not run_dir.is_dir():
            return None
    report_path = run_dir / "run_report.json"
    if not report_path.exists():
        return {"run_id": run_dir.name, "run_dir": str(run_dir), "status": "incomplete", "steps": []}
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["run_dir"] = str(run_dir)
    step_files = list(run_dir.glob("step_*.json"))
    report["step_files"] = [f.name for f in sorted(step_files)]
    return report


def list_runs(limit: int = 20, repo_root: Path | str | None = None) -> list[dict[str, Any]]:
    """List recent runs: run_id, chain_id, status, steps_total (from run_report.json)."""
    root = _repo_root(repo_root)
    runs_base = _runs_path(root)
    if not runs_base.exists():
        return []
    out: list[dict[str, Any]] = []
    for d in sorted(runs_base.iterdir(), key=lambda x: x.name, reverse=True):
        if not d.is_dir() or len(out) >= limit:
            break
        report_path = d / "run_report.json"
        if report_path.exists():
            try:
                r = json.loads(report_path.read_text(encoding="utf-8"))
                out.append({
                    "run_id": r.get("run_id", d.name),
                    "chain_id": r.get("chain_id"),
                    "status": r.get("status"),
                    "steps_total": r.get("steps_total", 0),
                    "run_dir": str(d),
                })
            except Exception:
                out.append({"run_id": d.name, "chain_id": None, "status": "?", "steps_total": 0, "run_dir": str(d)})
    return out

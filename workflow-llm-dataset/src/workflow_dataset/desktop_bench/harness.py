"""
M23I: Benchmark harness — run one benchmark or suite in simulate or real mode.
Mode is explicit; no silent fallback from real to simulate.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from workflow_dataset.desktop_bench.config import get_cases_dir, get_runs_dir
from workflow_dataset.desktop_bench.schema import DesktopBenchmarkCase, get_case, load_suite
from workflow_dataset.desktop_adapters import run_simulate, run_execute, get_sandbox_root
from workflow_dataset.task_demos.replay import replay_task_simulate
from workflow_dataset.capability_discovery.approval_registry import get_registry_path, load_approval_registry

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
        h = hashlib.sha256("".join(parts).encode()).hexdigest()[:16]
        return f"{prefix}{h}"


def run_benchmark(
    case_id: str,
    mode: str,  # "simulate" | "real"
    repo_root: Path | str | None = None,
    sandbox_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Run one benchmark case. Mode must be 'simulate' or 'real'; no silent fallback.
    Returns dict: run_id, run_path, benchmark_id, mode, outcome, approvals_checked, adapters_used,
    output_artifacts, errors, timing_seconds, case_result (per-step results).
    """
    root = Path(repo_root).resolve() if repo_root else None
    case = get_case(case_id, root)
    if not case:
        return {"error": f"Benchmark case not found: {case_id}"}

    if mode not in ("simulate", "real"):
        return {"error": f"Invalid mode: {mode}. Use 'simulate' or 'real'."}

    if mode == "real" and not case.real_mode_eligibility:
        return {
            "error": f"Benchmark {case_id} is not eligible for real mode (real_mode_eligibility=false). Use --mode simulate.",
            "benchmark_id": case_id,
        }

    # Approvals check for real mode
    reg_path = get_registry_path(root)
    approvals_checked: dict[str, Any] = {
        "registry_path": str(reg_path),
        "registry_exists": reg_path.exists() and reg_path.is_file(),
        "scopes_used": [],
    }
    if mode == "real" and not (reg_path.exists() and reg_path.is_file()):
        return {
            "error": "Real mode requires approval registry at data/local/capability_discovery/approvals.yaml.",
            "benchmark_id": case_id,
            "approvals_checked": approvals_checked,
        }

    runs_dir = get_runs_dir(root)
    run_id = stable_id("db", case_id, utc_now_iso(), prefix="")[:20]
    run_path = runs_dir / run_id
    run_path.mkdir(parents=True, exist_ok=True)
    case_out_dir = run_path / case_id
    case_out_dir.mkdir(parents=True, exist_ok=True)

    adapters_used: list[str] = []
    errors: list[str] = []
    step_results: list[dict[str, Any]] = []
    output_artifacts: list[str] = []
    t0 = time.perf_counter()

    if case.task_id:
        # Replay task: simulate only
        if mode == "real":
            return {
                "error": "Task replay is simulate-only; cannot run in real mode.",
                "benchmark_id": case_id,
                "run_path": str(run_path),
            }
        task, sim_results = replay_task_simulate(case.task_id, root)
        for i, sr in enumerate(sim_results):
            adapters_used.append(sr.adapter_id)
            step_results.append({
                "step_index": i,
                "adapter_id": sr.adapter_id,
                "action_id": sr.action_id,
                "success": sr.success,
                "message": sr.message,
                "mode": "simulate",
            })
            if not sr.success:
                errors.append(f"Step {i}: {sr.message}")
        outcome = "pass" if not errors else "fail"
    else:
        # Inline steps
        sandbox = sandbox_root or (get_sandbox_root(root) if root else get_sandbox_root())
        for i, step in enumerate(case.steps):
            adapter_id = str(step.get("adapter_id", ""))
            action_id = str(step.get("action_id", ""))
            params = dict(step.get("params") or {})
            adapters_used.append(adapter_id)
            if mode == "simulate":
                res = run_simulate(adapter_id, action_id, params)
                step_results.append({
                    "step_index": i,
                    "adapter_id": adapter_id,
                    "action_id": action_id,
                    "success": res.success,
                    "message": res.message,
                    "preview": res.preview[:500] if res.preview else "",
                    "mode": "simulate",
                })
                if not res.success:
                    errors.append(f"Step {i}: {res.message}")
            else:
                exec_res = run_execute(adapter_id, action_id, params, sandbox_root=sandbox, repo_root=root)
                step_results.append({
                    "step_index": i,
                    "adapter_id": adapter_id,
                    "action_id": action_id,
                    "success": exec_res.success,
                    "message": exec_res.message,
                    "output_keys": list(exec_res.output.keys()) if exec_res.output else [],
                    "mode": "real",
                })
                if not exec_res.success:
                    errors.append(f"Step {i}: {exec_res.message}")
                if exec_res.output:
                    art_path = case_out_dir / f"step_{i}_output.json"
                    out_data = {k: v for k, v in exec_res.output.items() if k != "content"}
                    if not out_data:
                        out_data = {"content_preview": str(exec_res.output.get("content", ""))[:200]}
                    elif "content" in exec_res.output and len(str(exec_res.output["content"])) > 500:
                        out_data["content_preview"] = str(exec_res.output["content"])[:200]
                    art_path.write_text(json.dumps(out_data, indent=2), encoding="utf-8")
                    output_artifacts.append(art_path.name)

    timing_seconds = round(time.perf_counter() - t0, 3)
    outcome = "pass" if not errors else "fail"

    manifest = {
        "run_id": run_id,
        "run_path": str(run_path),
        "benchmark_id": case_id,
        "mode": mode,
        "outcome": outcome,
        "approvals_checked": approvals_checked,
        "adapters_used": list(dict.fromkeys(adapters_used)),
        "output_artifacts": output_artifacts,
        "errors": errors,
        "timing_seconds": timing_seconds,
        "timestamp": utc_now_iso(),
        "case_result": {"steps": step_results},
    }
    (run_path / "run_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def run_suite(
    suite_name: str,
    mode: str,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """Run a benchmark suite. Returns run_id, run_path, suite, mode, cases (list of case run results), aggregate outcome."""
    root = Path(repo_root).resolve() if repo_root else None
    cases = load_suite(suite_name, root)
    if not cases:
        return {"error": f"Suite not found or empty: {suite_name}"}
    if mode not in ("simulate", "real"):
        return {"error": f"Invalid mode: {mode}. Use 'simulate' or 'real'."}

    runs_dir = get_runs_dir(root)
    run_id = stable_id("dbsuite", suite_name, utc_now_iso(), prefix="")[:20]
    run_path = runs_dir / run_id
    run_path.mkdir(parents=True, exist_ok=True)

    case_results: list[dict[str, Any]] = []
    all_errors: list[str] = []
    for c in cases:
        if mode == "real" and not c.real_mode_eligibility:
            case_results.append({
                "benchmark_id": c.benchmark_id,
                "outcome": "skip",
                "reason": "real_mode_eligibility=false",
            })
            continue
        m = run_benchmark(c.benchmark_id, mode, repo_root=root)
        if "error" in m:
            case_results.append({"benchmark_id": c.benchmark_id, "outcome": "error", "error": m["error"]})
            all_errors.append(m["error"])
        else:
            case_results.append({
                "benchmark_id": m["benchmark_id"],
                "outcome": m["outcome"],
                "run_path": m.get("run_path"),
                "errors": m.get("errors", []),
            })
            if m.get("errors"):
                all_errors.extend(m["errors"])

    aggregate_outcome = "pass" if not all_errors else "fail"
    manifest = {
        "run_id": run_id,
        "run_path": str(run_path),
        "suite": suite_name,
        "mode": mode,
        "timestamp": utc_now_iso(),
        "cases": case_results,
        "aggregate_outcome": aggregate_outcome,
    }
    (run_path / "run_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest

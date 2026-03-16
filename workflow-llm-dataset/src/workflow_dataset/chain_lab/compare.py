"""
M23A: Compare two chain runs (or variants). Read-only; no mutation. F2: output_inventory, artifact_diff.
"""

from __future__ import annotations

from typing import Any

from workflow_dataset.chain_lab.manifest import load_run_manifest
from workflow_dataset.chain_lab.report import resolve_run_id


def _output_inventory_from_manifest(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    """Build output inventory: [{ step_id, output_paths }] for each step."""
    inv: list[dict[str, Any]] = []
    for s in manifest.get("step_results") or []:
        inv.append({
            "step_id": s.get("step_id", ""),
            "step_index": s.get("step_index", 0),
            "output_paths": list(s.get("output_paths") or []),
        })
    return inv


def compare_chain_runs(
    run_id_a: str,
    run_id_b: str,
    repo_root: str | None = None,
    *,
    include_output_inventory: bool = True,
    include_artifact_diff: bool = False,
) -> dict[str, Any]:
    """
    Compare two chain runs: status, step count, step-wise status diff, failure summary.
    F2: output_inventory_a/b (step_id + output_paths per step); optionally artifact_diff
    (paths only in A, only in B) from flattened output paths.
    """
    resolved_a = resolve_run_id(run_id_a, repo_root) or run_id_a
    resolved_b = resolve_run_id(run_id_b, repo_root) or run_id_b
    ma = load_run_manifest(resolved_a, repo_root)
    mb = load_run_manifest(resolved_b, repo_root)
    out: dict[str, Any] = {
        "run_id_a": resolved_a,
        "run_id_b": resolved_b,
        "run_a": None,
        "run_b": None,
        "status_diff": None,
        "step_count_diff": None,
        "step_status_diff": [],
        "failure_diff": None,
    }
    if include_output_inventory:
        out["output_inventory_a"] = []
        out["output_inventory_b"] = []
    if include_artifact_diff:
        out["artifact_diff"] = None
    if not ma:
        out["run_a"] = "not_found"
        if not mb:
            out["run_b"] = "not_found"
        return out
    if not mb:
        out["run_b"] = "not_found"
        return out
    out["run_a"] = {"chain_id": ma.get("chain_id"), "variant": ma.get("variant_label"), "status": ma.get("status")}
    out["run_b"] = {"chain_id": mb.get("chain_id"), "variant": mb.get("variant_label"), "status": mb.get("status")}
    if include_output_inventory:
        out["output_inventory_a"] = _output_inventory_from_manifest(ma)
        out["output_inventory_b"] = _output_inventory_from_manifest(mb)
    sa, sb = ma.get("status", ""), mb.get("status", "")
    if sa != sb:
        out["status_diff"] = {"a": sa, "b": sb}
    steps_a = ma.get("step_results") or []
    steps_b = mb.get("step_results") or []
    out["step_count_diff"] = len(steps_a) - len(steps_b) if len(steps_a) != len(steps_b) else None
    for i in range(max(len(steps_a), len(steps_b))):
        ra = steps_a[i] if i < len(steps_a) else {}
        rb = steps_b[i] if i < len(steps_b) else {}
        sta, stb = ra.get("status", ""), rb.get("status", "")
        if sta != stb:
            out["step_status_diff"].append({
                "step_index": i,
                "step_id_a": ra.get("step_id", ""),
                "step_id_b": rb.get("step_id", ""),
                "status_a": sta,
                "status_b": stb,
            })
    fa, fb = ma.get("failure_summary"), mb.get("failure_summary")
    if fa != fb:
        out["failure_diff"] = {"a": fa, "b": fb}
    if include_artifact_diff:
        paths_a = set()
        paths_b = set()
        for s in steps_a:
            for p in s.get("output_paths") or []:
                paths_a.add(p)
        for s in steps_b:
            for p in s.get("output_paths") or []:
                paths_b.add(p)
        out["artifact_diff"] = {
            "only_in_a": sorted(paths_a - paths_b),
            "only_in_b": sorted(paths_b - paths_a),
            "common_count": len(paths_a & paths_b),
        }
    return out

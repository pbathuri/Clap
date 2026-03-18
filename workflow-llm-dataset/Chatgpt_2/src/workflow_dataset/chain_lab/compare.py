"""
M23A: Compare two chain runs (or variants). Read-only; no mutation. F2: output_inventory, artifact_diff.
F6: benchmark_view adds benchmark_summary for eval/review.
"""

from __future__ import annotations

from typing import Any

from workflow_dataset.chain_lab.manifest import (
    load_run_manifest,
    _duration_seconds,
    _final_artifacts_from_step_results,
)
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
    benchmark_view: bool = False,
) -> dict[str, Any]:
    """
    Compare two chain runs: status, step count, step-wise status diff, failure summary.
    F2: output_inventory_a/b (step_id + output_paths per step); optionally artifact_diff
    (paths only in A, only in B) from flattened output paths.
    F6: benchmark_view adds benchmark_summary (status, duration, artifact counts, one-line summary).
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
    out["run_a"] = {
        "chain_id": ma.get("chain_id"),
        "variant": ma.get("variant_label"),
        "status": ma.get("status"),
        "started_at": ma.get("started_at"),
        "ended_at": ma.get("ended_at"),
    }
    out["run_b"] = {
        "chain_id": mb.get("chain_id"),
        "variant": mb.get("variant_label"),
        "status": mb.get("status"),
        "started_at": mb.get("started_at"),
        "ended_at": mb.get("ended_at"),
    }
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
    if benchmark_view:
        dur_a = ma.get("duration_seconds") or _duration_seconds(ma.get("started_at"), ma.get("ended_at"))
        dur_b = mb.get("duration_seconds") or _duration_seconds(mb.get("started_at"), mb.get("ended_at"))
        fa = ma.get("final_artifacts") or _final_artifacts_from_step_results(steps_a)
        fb = mb.get("final_artifacts") or _final_artifacts_from_step_results(steps_b)
        out["benchmark_summary"] = {
            "run_id_a": resolved_a,
            "run_id_b": resolved_b,
            "status_a": ma.get("status"),
            "status_b": mb.get("status"),
            "duration_seconds_a": dur_a,
            "duration_seconds_b": dur_b,
            "artifact_count_a": len(fa),
            "artifact_count_b": len(fb),
            "summary_line": _benchmark_summary_line(
                resolved_a, resolved_b,
                ma.get("status"), mb.get("status"),
                dur_a, dur_b,
                len(fa), len(fb),
            ),
        }
    return out


def _benchmark_summary_line(
    id_a: str, id_b: str,
    status_a: str | None, status_b: str | None,
    dur_a: float | None, dur_b: float | None,
    count_a: int, count_b: int,
) -> str:
    """One-line summary for benchmark/review."""
    parts = [f"A={status_a or '?'} B={status_b or '?'}"]
    if dur_a is not None and dur_b is not None:
        parts.append(f"dur A={dur_a:.1f}s B={dur_b:.1f}s")
    parts.append(f"artifacts A={count_a} B={count_b}")
    return " | ".join(parts)


def benchmark_summary_text(diff: dict[str, Any]) -> str:
    """
    Return a short, benchmark/review-friendly text summary from a compare result.
    Use when benchmark_view was True. Returns empty string if no benchmark_summary.
    """
    bs = diff.get("benchmark_summary")
    if not bs:
        return ""
    lines = [
        f"Run A: {bs.get('run_id_a', '')}  status={bs.get('status_a')}  duration={bs.get('duration_seconds_a')}s  artifacts={bs.get('artifact_count_a', 0)}",
        f"Run B: {bs.get('run_id_b', '')}  status={bs.get('status_b')}  duration={bs.get('duration_seconds_b')}s  artifacts={bs.get('artifact_count_b', 0)}",
        bs.get("summary_line", ""),
    ]
    return "\n".join(lines)

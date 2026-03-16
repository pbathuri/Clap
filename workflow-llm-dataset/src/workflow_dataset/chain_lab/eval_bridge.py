"""
M23A-F6: Chain runs as eval/benchmark consumable.
Expose chain run manifests in a form the local eval harness can reference
(chain template id, variant, status, final artifacts, timings).
Internal and advisory; no change to eval harness contract.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.chain_lab.config import get_runs_dir
from workflow_dataset.chain_lab.manifest import (
    load_run_manifest,
    get_run_dir,
    _final_artifacts_from_step_results,
    _duration_seconds,
)
from workflow_dataset.chain_lab.manifest import list_run_ids as _list_run_ids
from workflow_dataset.chain_lab.report import resolve_run_id


def list_chain_runs_for_eval(
    limit: int = 50,
    repo_root: Path | str | None = None,
) -> list[dict[str, Any]]:
    """
    List chain runs in eval-consumable shape: run_id, chain_template_id, variant_id,
    status, final_artifacts, started_at, ended_at, duration_seconds, run_path.
    For use by the local eval/benchmark layer to reference chain runs or chain templates.
    """
    root = Path(repo_root).resolve() if repo_root else None
    run_ids = _list_run_ids(repo_root=root, limit=limit)
    runs_dir = get_runs_dir(root)
    out: list[dict[str, Any]] = []
    for rid in run_ids:
        manifest = load_run_manifest(rid, repo_root=root)
        if not manifest:
            continue
        run_path = runs_dir / rid
        final_artifacts = manifest.get("final_artifacts")
        if final_artifacts is None:
            final_artifacts = _final_artifacts_from_step_results(manifest.get("step_results") or [])
        duration = manifest.get("duration_seconds")
        if duration is None:
            duration = _duration_seconds(manifest.get("started_at"), manifest.get("ended_at"))
        out.append({
            "run_id": manifest.get("run_id", rid),
            "chain_template_id": manifest.get("chain_template_id") or manifest.get("chain_id", ""),
            "chain_id": manifest.get("chain_id", ""),
            "variant_id": manifest.get("variant_id") or manifest.get("variant_label", ""),
            "variant_label": manifest.get("variant_label", ""),
            "status": manifest.get("status", ""),
            "final_artifacts": list(final_artifacts),
            "started_at": manifest.get("started_at"),
            "ended_at": manifest.get("ended_at"),
            "duration_seconds": duration,
            "run_path": str(run_path),
        })
    return out


def get_chain_run_for_eval(
    run_id: str,
    repo_root: Path | str | None = None,
) -> dict[str, Any] | None:
    """
    Return one chain run in eval-consumable shape, or None if not found.
    run_id may be 'latest' (resolved to most recent run).
    """
    resolved = resolve_run_id(run_id, repo_root=repo_root) or run_id
    manifest = load_run_manifest(resolved, repo_root=repo_root)
    if not manifest:
        return None
    root = Path(repo_root).resolve() if repo_root else None
    run_path = get_run_dir(resolved, repo_root=root, create=False)
    final_artifacts = manifest.get("final_artifacts")
    if final_artifacts is None:
        final_artifacts = _final_artifacts_from_step_results(manifest.get("step_results") or [])
    duration = manifest.get("duration_seconds")
    if duration is None:
        duration = _duration_seconds(manifest.get("started_at"), manifest.get("ended_at"))
    return {
        "run_id": manifest.get("run_id", resolved),
        "chain_template_id": manifest.get("chain_template_id") or manifest.get("chain_id", ""),
        "chain_id": manifest.get("chain_id", ""),
        "variant_id": manifest.get("variant_id") or manifest.get("variant_label", ""),
        "variant_label": manifest.get("variant_label", ""),
        "status": manifest.get("status", ""),
        "final_artifacts": list(final_artifacts),
        "started_at": manifest.get("started_at"),
        "ended_at": manifest.get("ended_at"),
        "duration_seconds": duration,
        "run_path": str(run_path),
    }

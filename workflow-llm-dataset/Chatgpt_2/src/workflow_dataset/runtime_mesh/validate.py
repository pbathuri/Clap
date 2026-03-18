"""
M23S: Runtime/model compatibility validation. No rewrite; no mandatory backends.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.runtime_mesh.backend_registry import list_backend_profiles
from workflow_dataset.runtime_mesh.model_catalog import load_model_catalog
from workflow_dataset.runtime_mesh.policy import TASK_CLASS_POLICY, recommend_for_task_class, compatibility_for_model


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd()


def run_runtime_validate(
    repo_root: Path | str | None = None,
    include_models: bool = True,
) -> dict[str, Any]:
    """
    Validate model/runtime compatibility: per task class and optionally per model in catalog.
    Returns: passed, task_class_results[], model_results[], errors[], summary.
    """
    root = _repo_root(repo_root)
    task_class_results: list[dict[str, Any]] = []
    model_results: list[dict[str, Any]] = []
    errors: list[str] = []
    all_passed = True

    for task_class in TASK_CLASS_POLICY:
        rec = recommend_for_task_class(task_class, root)
        missing = rec.get("missing") or []
        backend_ok = rec.get("backend_status") in ("available", "configured")
        task_class_results.append({
            "task_class": task_class,
            "backend_id": rec.get("backend_id"),
            "backend_status": rec.get("backend_status"),
            "passed": backend_ok and len(missing) == 0,
            "missing": missing,
        })
        if not backend_ok or missing:
            all_passed = False

    if include_models:
        catalog = load_model_catalog(root)
        for m in catalog[:30]:
            comp = compatibility_for_model(m.model_id, root)
            backend_ok = comp.get("backend_status") in ("available", "configured")
            model_results.append({
                "model_id": m.model_id,
                "backend_family": m.backend_family,
                "backend_status": comp.get("backend_status"),
                "passed": backend_ok,
                "in_catalog": comp.get("in_catalog", True),
            })
            if not backend_ok and comp.get("in_catalog"):
                all_passed = False

    return {
        "passed": all_passed,
        "task_class_results": task_class_results,
        "model_results": model_results,
        "errors": errors,
        "summary": "All task classes and models compatible." if all_passed else "Some task classes or models have missing/unsupported backends.",
    }


def format_validation_report(result: dict[str, Any]) -> str:
    """Human-readable compatibility validation report."""
    lines = [
        "=== Runtime compatibility validation ===",
        "",
        result.get("summary", ""),
        "",
        "[Task class → backend]",
    ]
    for r in result.get("task_class_results") or []:
        status = "PASS" if r.get("passed") else "FAIL"
        lines.append(f"  {status}  {r.get('task_class')}  backend={r.get('backend_id')}  status={r.get('backend_status')}")
        if r.get("missing"):
            lines.append(f"       missing: {', '.join(r['missing'][:3])}")
    if result.get("model_results"):
        lines.append("")
        lines.append("[Model → backend]")
        for r in (result.get("model_results") or [])[:15]:
            status = "PASS" if r.get("passed") else "FAIL"
            lines.append(f"  {status}  {r.get('model_id')}  backend={r.get('backend_family')}  status={r.get('backend_status')}")
        if len(result.get("model_results") or []) > 15:
            lines.append(f"  ... and {len(result['model_results']) - 15} more")
    if result.get("errors"):
        lines.append("")
        lines.append("[Errors]")
        for e in result["errors"]:
            lines.append(f"  - {e}")
    lines.append("")
    lines.append("(Backend-agnostic; no mandatory backends. Optional backends are opt-in.)")
    return "\n".join(lines)

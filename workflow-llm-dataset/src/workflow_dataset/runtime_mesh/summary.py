"""
M23S: Runtime summary — available backends, which product surfaces (task classes) depend on which runtime.
Backend-agnostic; no rewrite; no mandatory backends.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.runtime_mesh.backend_registry import list_backend_profiles
from workflow_dataset.runtime_mesh.policy import TASK_CLASS_POLICY, recommend_for_task_class


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd()


def build_runtime_summary(repo_root: Path | str | None = None) -> dict[str, Any]:
    """
    Summarize available local backends and which product surfaces (task classes) depend on them.
    Returns: backends[], task_class_dependencies[], available_backend_ids, missing_backend_ids.
    """
    root = _repo_root(repo_root)
    backends = list_backend_profiles(root)
    available = [b.backend_id for b in backends if b.status in ("available", "configured")]
    missing = [b.backend_id for b in backends if b.status == "missing"]
    unsupported = [b.backend_id for b in backends if b.status == "unsupported"]

    backend_list: list[dict[str, Any]] = []
    for b in backends:
        backend_list.append({
            "backend_id": b.backend_id,
            "backend_family": b.backend_family,
            "status": b.status,
            "local": b.local,
            "install_prerequisites": b.install_prerequisites[:5],
            "notes": b.notes[:200] if b.notes else "",
        })

    task_class_dependencies: list[dict[str, Any]] = []
    for task_class in TASK_CLASS_POLICY:
        rec = recommend_for_task_class(task_class, root)
        task_class_dependencies.append({
            "task_class": task_class,
            "backend_id": rec.get("backend_id"),
            "backend_status": rec.get("backend_status"),
            "model_class": rec.get("model_class"),
            "missing": rec.get("missing", []),
        })

    return {
        "backends": backend_list,
        "task_class_dependencies": task_class_dependencies,
        "available_backend_ids": available,
        "missing_backend_ids": missing,
        "unsupported_backend_ids": unsupported,
        "backend_count": len(backends),
    }


def format_runtime_summary(summary: dict[str, Any] | None = None, repo_root: Path | str | None = None) -> str:
    """Human-readable runtime summary report."""
    if summary is None:
        summary = build_runtime_summary(repo_root)
    lines = [
        "=== Runtime summary ===",
        "",
        "[Backends]",
    ]
    for b in summary.get("backends") or []:
        lines.append(f"  {b.get('backend_id')}  family={b.get('backend_family')}  status={b.get('status')}  local={b.get('local')}")
    lines.append("")
    lines.append("[Product surfaces (task classes) → runtime]")
    for dep in summary.get("task_class_dependencies") or []:
        tc = dep.get("task_class", "")
        bid = dep.get("backend_id") or "(none)"
        status = dep.get("backend_status", "")
        missing = dep.get("missing") or []
        lines.append(f"  {tc} → backend={bid}  status={status}")
        if missing:
            lines.append(f"    missing: {', '.join(missing[:3])}")
    lines.append("")
    lines.append(f"Available: {summary.get('available_backend_ids', [])}  Missing: {summary.get('missing_backend_ids', [])}  Unsupported: {summary.get('unsupported_backend_ids', [])}")
    return "\n".join(lines)

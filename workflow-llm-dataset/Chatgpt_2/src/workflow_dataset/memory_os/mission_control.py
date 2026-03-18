"""
M44D: Mission control visibility — active namespaces, top surfaces, weak-memory warnings, recent misses, next review.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.memory_os.surfaces import list_surfaces


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def memory_os_slice(repo_root: Path | str | None = None) -> dict[str, Any]:
    """
    Mission-control slice for memory OS: active namespaces, surfaces in use, weak-memory count,
    recent retrieval misses (placeholder), next recommended memory review.
    """
    root = _repo_root(repo_root)
    out: dict[str, Any] = {
        "active_namespaces": ["personal", "product", "learning", "cursor"],
        "surfaces": [s.to_dict() for s in list_surfaces()],
        "top_surfaces_in_use": [],
        "weak_memory_warnings_count": 0,
        "recent_retrieval_misses_count": 0,
        "next_recommended_memory_review": "",
    }

    try:
        from workflow_dataset.memory_fusion.review import list_weak_memories
        weak = list_weak_memories(confidence_below=0.6, limit=100, repo_root=root)
        out["weak_memory_warnings_count"] = len(weak)
        if weak:
            out["next_recommended_memory_review"] = "Review weak memory links: workflow-dataset memory-os weak"
    except Exception:
        pass

    try:
        from workflow_dataset.memory_substrate.store import get_status
        st = get_status(repo_root=root)
        out["substrate_units_count"] = st.get("units_count", 0)
        out["substrate_sessions_count"] = st.get("sessions_count", 0)
    except Exception:
        out["substrate_units_count"] = 0
        out["substrate_sessions_count"] = 0

    out["top_surfaces_in_use"] = [s["surface_id"] for s in out["surfaces"]][:5]
    return out


def memory_os_status(repo_root: Path | str | None = None) -> dict[str, Any]:
    """Status for CLI memory-os status."""
    slice_data = memory_os_slice(repo_root)
    return {
        "namespaces": slice_data["active_namespaces"],
        "surfaces_count": len(slice_data["surfaces"]),
        "weak_memory_warnings": slice_data["weak_memory_warnings_count"],
        "substrate_units": slice_data.get("substrate_units_count", 0),
        "substrate_sessions": slice_data.get("substrate_sessions_count", 0),
        "next_review": slice_data.get("next_recommended_memory_review", ""),
    }

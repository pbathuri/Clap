"""
M43I–M43L: Cursor bridge — safe notes/config for using the same local memory substrate from Cursor.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.memory_substrate.models import MEMORY_SCOPE_PRODUCTION_SAFE, MEMORY_SCOPE_EXPERIMENTAL


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def build_cursor_bridge_report(repo_root: Path | str | None = None) -> dict[str, Any]:
    """
    Report for Cursor: paths to local memory-relevant dirs, production-safe vs experimental,
    env vars, and usage notes. Read-only; no automatic write from Cursor to product memory.
    """
    root = _root(repo_root)
    data_local = root / "data" / "local"

    production_safe_paths = [
        str((data_local / "outcomes").resolve()),
        str((data_local / "corrections" / "events").resolve()) if (data_local / "corrections").exists() else None,
    ]
    production_safe_paths = [p for p in production_safe_paths if p]

    experimental_paths = [
        str((data_local / "memory_substrate").resolve()),
        str((data_local / "memory_fusion").resolve()),
        str((data_local / "learning_lab").resolve()),
        str((data_local / "candidate_model_studio").resolve()),
        str((data_local / "safe_adaptation").resolve()),
        str((data_local / "benchmark_board").resolve()),
        str((data_local / "eval" / "runs").resolve()) if (data_local / "eval").exists() else None,
    ]
    experimental_paths = [p for p in experimental_paths if p]

    return {
        "cursor_bridge_version": "1.0",
        "repo_root": str(root.resolve()),
        "data_local": str(data_local.resolve()),
        "production_safe_paths": production_safe_paths,
        "production_safe_note": "Read-only from Cursor recommended. Writes to production memory require explicit operator approval and review.",
        "experimental_paths": experimental_paths,
        "experimental_note": "Learning lab, candidate model studio, benchmarks. Safe for Cursor to read; writes still reviewable.",
        "env_suggestions": {
            "WORKFLOW_DATASET_REPO_ROOT": str(root.resolve()),
            "WORKFLOW_MEMORY_DATA_LOCAL": str(data_local.resolve()),
        },
        "usage_notes": [
            "Use same repo root (WORKFLOW_DATASET_REPO_ROOT) so Cursor and workflow-dataset CLI see the same data/local.",
            "Memory-backed slices: learning-lab memory-slices, then use memory_slice_id in experiments or candidate creation.",
            "Do not write to production_safe paths from Cursor without explicit review; use experimental paths for learning/candidates.",
        ],
        "cli_commands": [
            "workflow-dataset memory status             # substrate status",
            "workflow-dataset memory ingest/retrieve    # substrate ingest and query",
            "workflow-dataset memory cursor-bridge      # this report",
            "workflow-dataset learning-lab memory-slices  # list memory-backed slices for experiments",
            "workflow-dataset benchmarks memory-compare  # compare with memory-aware slice tag",
        ],
    }

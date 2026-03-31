"""
Snapshot/shaping utilities for local operator (shell, edge-desktop, console).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.local_operator.summary import build_operator_state_summary

__all__ = [
    "build_operator_state_summary",
    "export_operator_summary_for_surfaces",
]


def export_operator_summary_for_surfaces(repo_root: Path | str | None = None) -> dict[str, Any]:
    """
    Stable, documented shape for CLI / snapshot fetchers / investor surfaces.
    Same payload as build_operator_state_summary; explicit name for integration contracts.
    """
    return build_operator_state_summary(repo_root)

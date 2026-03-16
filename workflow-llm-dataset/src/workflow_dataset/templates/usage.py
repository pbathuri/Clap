"""
M22E-F6: Template usage summary — aggregate template-driven runs from workspaces (and optional pilot sessions).
Local-only; no cloud or heavy analytics.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def template_usage_summary(
    workspaces_root: str | Path = "data/local/workspaces",
    repo_root: Path | str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    """
    Scan reporting workspaces and aggregate by template_id.
    Returns: counts_by_template (template_id -> run count), recent_runs (list of {template_id, run_id, workspace_path, timestamp}),
    total_template_runs, total_runs.
    """
    if repo_root is not None:
        root = Path(repo_root)
    else:
        try:
            from workflow_dataset.path_utils import get_repo_root
            root = Path(get_repo_root())
        except Exception:
            root = Path.cwd()
    ws_root = root / workspaces_root if not Path(workspaces_root).is_absolute() else Path(workspaces_root)
    if not ws_root.exists():
        return {
            "counts_by_template": {},
            "recent_runs": [],
            "total_template_runs": 0,
            "total_runs": 0,
        }
    from workflow_dataset.release.reporting_workspaces import list_reporting_workspaces
    workspaces = list_reporting_workspaces(ws_root, limit=limit)
    counts: dict[str, int] = {}
    recent_runs: list[dict[str, Any]] = []
    total_template_runs = 0
    for inv in workspaces:
        tid = inv.get("template_id")
        if tid:
            counts[tid] = counts.get(tid, 0) + 1
            total_template_runs += 1
            recent_runs.append({
                "template_id": tid,
                "template_version": inv.get("template_version"),
                "run_id": inv.get("run_id"),
                "workspace_path": inv.get("workspace_path"),
                "timestamp": inv.get("timestamp"),
                "workflow": inv.get("workflow"),
            })
    return {
        "counts_by_template": dict(sorted(counts.items(), key=lambda x: -x[1])),
        "recent_runs": recent_runs[:50],
        "total_template_runs": total_template_runs,
        "total_runs": len(workspaces),
    }

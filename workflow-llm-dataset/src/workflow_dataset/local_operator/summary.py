"""
Shaped summary for CLI/TUI/shell surfaces.
Derives from local operator core state; does not mutate core state.
"""

from __future__ import annotations

from typing import Any
from pathlib import Path

from workflow_dataset.local_operator.state_store import load_operator_state
from workflow_dataset.local_operator.readiness import build_machine_readiness, build_operator_readiness
from workflow_dataset.local_operator.task_store import list_recent_task_run_summaries, list_task_runs


def _repo_root(root: Path | str | None) -> Path:
    if root is not None:
        return Path(root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _tool_counts(tools: list[dict[str, Any]]) -> dict[str, int]:
    def _count(key: str) -> int:
        return len([t for t in tools if t.get(key)])
    return {
        "total": len(tools),
        "installed": _count("installed"),
        "inferred": _count("inferred"),
        "actively_relevant": _count("actively_relevant"),
        "adapter_supported": _count("adapter_supported"),
        "permission_ready": _count("permission_ready"),
    }


def build_operator_state_summary(repo_root: Path | str | None = None) -> dict[str, Any]:
    root = _repo_root(repo_root)
    state = load_operator_state(root)
    machine_readiness = build_machine_readiness(root)
    operator_readiness = build_operator_readiness(root)

    approved_folders = list(state.get("approved_folders") or [])
    workflow_tree = list(state.get("workflow_tree") or [])
    tools = list(state.get("tool_registry") or [])
    actions = list(state.get("action_proposals") or [])

    task_runs_recent = list_recent_task_run_summaries(root, limit=15)
    task_runs_total = len(list_task_runs(root))

    return {
        "machine_readiness": machine_readiness,
        "operator_readiness": operator_readiness,
        "approved_folders": {
            "count": len(approved_folders),
            "items": approved_folders[:10],
        },
        "workflow_tree": {
            "node_count": len(workflow_tree),
            "roots": [n.get("node_id") for n in workflow_tree if n.get("node_type") == "root"][:10],
        },
        "tool_registry": {
            **_tool_counts(tools),
            "items": tools[:10],
        },
        "action_proposals": {
            "count": len(actions),
            "items": actions[:10],
        },
        "session_trust": state.get("session_trust") or {},
        "capability_trust": state.get("capability_trust") or [],
        "last_execution": operator_readiness.get("last_execution") or state.get("last_execution"),
        "last_task_plan_id": state.get("last_task_plan_id"),
        "last_task_run_id": state.get("last_task_run_id"),
        "last_task_run": state.get("last_task_run"),
        "task_runs": {
            "total_stored": task_runs_total,
            "recent": task_runs_recent,
        },
        "updated_at": state.get("updated_at", ""),
    }


def build_local_operator_cli_summary(repo_root: Path | str | None = None, *, as_json: bool = False) -> dict[str, Any]:
    """Full user-facing summary dict (CLI `local summary` / --json)."""
    s = build_operator_state_summary(repo_root)
    out = {
        "readiness": {
            "machine": s["machine_readiness"],
            "operator": s["operator_readiness"],
            "capability_trust": s["capability_trust"],
        },
        "approved_folders": s["approved_folders"],
        "workflow_tree": s["workflow_tree"],
        "tool_registry": s["tool_registry"],
        "action_proposals": s["action_proposals"],
        "last_execution": s.get("last_execution"),
        "last_task_run": s.get("last_task_run"),
        "task_runs": s.get("task_runs"),
        "updated_at": s.get("updated_at"),
    }
    return out

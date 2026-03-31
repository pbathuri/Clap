"""
Single JSON snapshot for Edge Operator Desktop prototype.
"""

from __future__ import annotations

import os
import threading
from pathlib import Path
from typing import Any

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone

    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root

        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


_SNAPSHOT_TIMEOUT_SEC = float(os.environ.get("EDGE_DESKTOP_SNAPSHOT_TIMEOUT_SEC", "12"))


def _run_with_timeout(label: str, fn) -> tuple[Any | None, str | None]:
    """Run a fetcher with a bounded timeout to avoid hanging snapshots."""
    out: list[Any | None] = [None]
    err: list[BaseException | None] = [None]

    def _run() -> None:
        try:
            out[0] = fn()
        except BaseException as e:
            err[0] = e

    if _SNAPSHOT_TIMEOUT_SEC <= 0:
        try:
            return fn(), None
        except BaseException as e:
            return None, str(e)[:500]
    t = threading.Thread(target=_run, daemon=True, name=f"edge_snapshot_{label}")
    t.start()
    t.join(timeout=_SNAPSHOT_TIMEOUT_SEC)
    if t.is_alive():
        return None, f"{label} timed out after {_SNAPSHOT_TIMEOUT_SEC:.0f}s"
    if err[0] is not None:
        return None, str(err[0])[:500]
    return out[0], None


def build_edge_desktop_snapshot(repo_root: Path | str | None = None) -> dict[str, Any]:
    root = _root(repo_root)
    try:
        from workflow_dataset.live_desktop_adapter import build_live_adapter_snapshot, RefreshPolicy

        pol = RefreshPolicy(
            timeout_seconds=min(6.0, _SNAPSHOT_TIMEOUT_SEC),
            presenter_fast_path=False,
            merge_last_good_cache=True,
            skip_slow_text_fetchers=False,
            max_parallel_wait_seconds=min(25.0, _SNAPSHOT_TIMEOUT_SEC * 2),
        )
        out: dict[str, Any] = build_live_adapter_snapshot(repo_root=root, policy=pol)
    except Exception as e:
        out = {
            "generated_at": utc_now_iso(),
            "repo_root": str(root),
            "sources_ok": [],
            "errors": {"live_adapter": str(e)[:500]},
            "readiness": None,
            "bootstrap_last": None,
            "onboarding_ready": None,
            "workspace_home": None,
            "workspace_home_text": None,
            "day_status": None,
            "day_status_text": None,
            "guidance_next_action": None,
            "operator_summary": None,
            "inbox": [],
        }
    # Keep adapter meta out of the base snapshot unless explicitly requested elsewhere.
    out.pop("adapter_meta", None)
    out["repo_root"] = str(root)
    out.setdefault("errors", {})
    out.setdefault("sources_ok", [])

    inv_home, err = _run_with_timeout(
        "investor_mission_control_home",
        lambda: __import__("workflow_dataset.investor_mission_control", fromlist=["build_mission_control_investor_home"])
        .build_mission_control_investor_home(root)
        .to_dict(),
    )
    if err:
        out["errors"]["investor_mission_control_home"] = err
    elif inv_home is not None:
        out["investor_mission_control_home"] = inv_home
        out["sources_ok"].append("investor_mission_control_home")

    # Shallow supervised task-run surface for shells (full detail remains in local_operator_summary).
    try:
        from workflow_dataset.local_operator.summary import build_operator_state_summary

        osum = build_operator_state_summary(root)
        tr = osum.get("task_runs") or {}
        out["supervised_task_run"] = {
            "last_task_run": osum.get("last_task_run"),
            "recent": (tr.get("recent") or [])[:10],
            "total_stored": tr.get("total_stored", 0),
        }
        out["sources_ok"].append("supervised_task_run")
    except Exception as e:
        out["errors"]["supervised_task_run"] = str(e)[:500]

    return out

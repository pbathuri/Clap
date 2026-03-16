"""
Devlab dev loop: one-shot run (evidence, repo reports, model compare, memo, tests); save artifacts.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.devlab.config import get_devlab_root, get_loop_artifact_path, get_reports_dir


def _read_loop_status(root: Path | str | None = None) -> dict[str, Any]:
    path = get_loop_artifact_path("loop_status.json", root)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_loop_status(data: dict[str, Any], root: Path | str | None = None) -> None:
    path = get_loop_artifact_path("loop_status.json", root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def run_loop(
    workflow: str = "weekly_status",
    providers: list[str] | None = None,
    root: Path | str | None = None,
) -> dict[str, Any]:
    """Run one-shot dev loop: write devlab_report.md, next_patch_plan.md; set running then clear."""
    root = Path(root) if root else get_devlab_root()
    _write_loop_status({"running": True}, root)
    try:
        report_path = get_loop_artifact_path("devlab_report.md", root)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text("# Devlab report\n\n(One-shot run; no external execution.)\n", encoding="utf-8")
        plan_path = get_loop_artifact_path("next_patch_plan.md", root)
        plan_path.write_text("# Next patch plan\n\n(Advisory.)\n", encoding="utf-8")
        _write_loop_status({"running": False, "devlab_report": str(report_path), "next_patch_plan": str(plan_path)}, root)
        return _read_loop_status(root)
    except Exception:
        _write_loop_status({"running": False}, root)
        raise


def loop_status(root: Path | str | None = None) -> dict[str, Any]:
    """Return loop status: running, devlab_report, next_patch_plan, etc."""
    return _read_loop_status(root)


def stop_loop(root: Path | str | None = None) -> None:
    """Clear running flag."""
    data = _read_loop_status(root)
    data["running"] = False
    _write_loop_status(data, root)

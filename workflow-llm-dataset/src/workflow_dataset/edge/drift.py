"""
M23B-F5: Readiness drift detection — compare current checks to previous snapshot.
Surfaces what changed, got worse, improved. Local-only; no daemon.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.edge.checks import run_readiness_checks, checks_summary
from workflow_dataset.edge.profile import build_edge_profile
from workflow_dataset.edge.history import (
    load_previous_snapshot,
    snapshot_from_checks,
)
from workflow_dataset.utils.dates import utc_now_iso

EDGE_OUTPUT_DIR = "data/local/edge"


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root())
    except Exception:
        return Path.cwd().resolve()


def compute_drift(
    repo_root: Path | str | None = None,
    config_path: str = "configs/settings.yaml",
) -> dict[str, Any]:
    """
    Run checks now (current), load previous snapshot from history, compare.
    Returns: current_ready, previous_ready, worse (check_ids that went passed→failed),
    improved (failed→passed), unchanged_failed, current_snapshot, previous_snapshot, has_drift.
    """
    root = _repo_root(repo_root)
    checks = run_readiness_checks(repo_root=root, config_path=config_path)
    summary = checks_summary(checks)
    profile = build_edge_profile(repo_root=root, config_path=config_path)
    current = snapshot_from_checks(checks, summary, profile, utc_now_iso())
    previous = load_previous_snapshot(repo_root=root)

    result: dict[str, Any] = {
        "current_ready": summary.get("ready", False),
        "previous_ready": None,
        "worse": [],
        "improved": [],
        "unchanged_failed": [],
        "unchanged_passed": [],
        "current_snapshot": current,
        "previous_snapshot": previous,
        "has_drift": False,
    }
    if not previous:
        result["next_command"] = "Run: workflow-dataset edge check-now (no previous snapshot to compare)."
        return result

    result["previous_ready"] = previous.get("ready", False)
    prev_checks = {c["check_id"]: c for c in (previous.get("checks") or [])}
    for c in current.get("checks") or []:
        cid = c.get("check_id")
        if not cid:
            continue
        now_passed = c.get("passed", False)
        prev = prev_checks.get(cid)
        if not prev:
            if not now_passed:
                result["worse"].append(cid)
            continue
        prev_passed = prev.get("passed", False)
        if prev_passed and not now_passed:
            result["worse"].append(cid)
        elif not prev_passed and now_passed:
            result["improved"].append(cid)
        elif not now_passed:
            result["unchanged_failed"].append(cid)
        else:
            result["unchanged_passed"].append(cid)

    result["has_drift"] = bool(result["worse"] or result["improved"])

    if result["worse"]:
        result["next_command"] = "Run: workflow-dataset edge missing-deps to see required/optional failures; fix required checks then workflow-dataset edge check-now."
    elif result["improved"]:
        result["next_command"] = "Run: workflow-dataset edge readiness to confirm; workflow-dataset edge check-now to record."
    else:
        result["next_command"] = "Run: workflow-dataset edge check-now to record current state; workflow-dataset edge readiness for full report."

    return result


def generate_drift_report(
    output_path: Path | str | None = None,
    repo_root: Path | str | None = None,
    config_path: str = "configs/settings.yaml",
) -> Path:
    """Compute drift and write a readable markdown report. Returns path to report."""
    root = _repo_root(repo_root)
    out_dir = root / EDGE_OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    path = output_path or (out_dir / "readiness_drift_report.md")
    path = Path(path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)

    drift = compute_drift(repo_root=root, config_path=config_path)

    lines = [
        "# Readiness Drift Report",
        "",
        "Comparison of current readiness checks vs the last recorded snapshot. Local-only; operator-started.",
        "",
    ]
    prev = drift.get("previous_snapshot")
    if not prev:
        lines.append("**No previous snapshot found.** Record one with: `workflow-dataset edge check-now`")
        lines.append("")
        path.write_text("\n".join(lines), encoding="utf-8")
        return path

    lines.append("## Outcome")
    lines.append("")
    cur_ready = drift.get("current_ready")
    prev_ready = drift.get("previous_ready")
    lines.append(f"- **Current:** {'Ready' if cur_ready else 'Not ready'}")
    lines.append(f"- **Previous:** {'Ready' if prev_ready else 'Not ready'}")
    lines.append(f"- **Drift:** {'Yes' if drift.get('has_drift') else 'No change'}")
    lines.append("")

    if drift.get("worse"):
        lines.append("## What got worse")
        lines.append("")
        lines.append("These checks passed before and now fail (fix to restore readiness):")
        lines.append("")
        for cid in drift["worse"]:
            lines.append(f"- **{cid}**")
        lines.append("")

    if drift.get("improved"):
        lines.append("## What improved")
        lines.append("")
        for cid in drift["improved"]:
            lines.append(f"- **{cid}**")
        lines.append("")

    if drift.get("unchanged_failed"):
        lines.append("## Still failing (unchanged)")
        lines.append("")
        for cid in drift["unchanged_failed"][:15]:
            lines.append(f"- {cid}")
        if len(drift["unchanged_failed"]) > 15:
            lines.append(f"- ... and {len(drift['unchanged_failed']) - 15} more")
        lines.append("")

    lines.append("## Next command")
    lines.append("")
    lines.append(drift.get("next_command", "workflow-dataset edge check-now"))
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path

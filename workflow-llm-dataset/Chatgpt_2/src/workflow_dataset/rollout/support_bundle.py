"""
M24F: Support bundle — gather environment health, runtime mesh, pack state,
acceptance result, trust state, last reports/manifests, issue summary template.
Output to a local directory.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from workflow_dataset.rollout.issues import format_issues_report


def _repo_root(root: Path | str | None) -> Path:
    if root is not None:
        return Path(root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def build_support_bundle_summary_only(repo_root: Path | str | None = None) -> dict[str, Any]:
    """Build the same summary dict as build_support_bundle but without writing any files. For issues report."""
    root = _repo_root(repo_root)
    summary: dict[str, Any] = {}
    try:
        from workflow_dataset.mission_control.state import get_mission_control_state
        state = get_mission_control_state(repo_root=root)
    except Exception as e:
        state = {"error": str(e)}
    summary["environment_health"] = state.get("environment_health") or {}
    summary["runtime_mesh"] = state.get("runtime_mesh") or {}
    summary["starter_kits"] = state.get("starter_kits") or {}
    summary["trust_cockpit"] = state.get("trust_cockpit") or {}
    try:
        from workflow_dataset.acceptance.storage import load_latest_run
        summary["latest_acceptance"] = load_latest_run(repo_root=root) or {}
    except Exception:
        summary["latest_acceptance"] = {}
    try:
        from workflow_dataset.rollout.tracker import load_rollout_state
        summary["rollout_state"] = load_rollout_state(repo_root=root)
    except Exception:
        summary["rollout_state"] = {}
    return summary


def build_support_bundle(
    repo_root: Path | str | None = None,
    output_dir: Path | str | None = None,
) -> dict[str, Any]:
    """
    Build local support bundle: environment health, runtime mesh, starter kit state,
    latest acceptance result, trust state, paths to last reports, issue template.
    Writes to output_dir (default data/local/rollout/support_bundle_<timestamp>).
    Returns summary dict with paths and keys.
    """
    root = _repo_root(repo_root)
    from workflow_dataset.utils.dates import utc_now_iso
    try:
        t = utc_now_iso().replace(":", "-").replace(".", "-")[:19]
    except Exception:
        from datetime import datetime, timezone
        t = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")
    default_out = root / "data/local/rollout" / f"support_bundle_{t}"
    out = Path(output_dir).resolve() if output_dir else default_out
    out.mkdir(parents=True, exist_ok=True)

    summary: dict[str, Any] = {"output_dir": str(out), "generated_at": t}

    # Mission control state (single call; reuse for mesh, kits, trust)
    state: dict[str, Any] = {}
    try:
        from workflow_dataset.mission_control.state import get_mission_control_state
        state = get_mission_control_state(repo_root=root)
    except Exception as e:
        state = {"error": str(e)}

    # Environment health
    env = state.get("environment_health") or {}
    summary["environment_health"] = env
    (out / "environment_health.json").write_text(json.dumps(env, indent=2), encoding="utf-8")

    # Runtime mesh summary
    mesh = state.get("runtime_mesh") or {}
    summary["runtime_mesh"] = mesh
    (out / "runtime_mesh.json").write_text(json.dumps(mesh, indent=2), encoding="utf-8")

    # Starter kits / value pack state
    kits = state.get("starter_kits") or {}
    summary["starter_kits"] = kits
    (out / "starter_kits.json").write_text(json.dumps(kits, indent=2), encoding="utf-8")

    # Latest acceptance result
    try:
        from workflow_dataset.acceptance.storage import load_latest_run
        latest = load_latest_run(repo_root=root)
        summary["latest_acceptance"] = latest
        (out / "latest_acceptance.json").write_text(json.dumps(latest or {}, indent=2), encoding="utf-8")
    except Exception as e:
        summary["latest_acceptance"] = {"error": str(e)}
        (out / "latest_acceptance.json").write_text(json.dumps({"error": str(e)}, indent=2), encoding="utf-8")

    # Trust state
    trust = state.get("trust_cockpit") or {}
    summary["trust_cockpit"] = trust
    (out / "trust_cockpit.json").write_text(json.dumps(trust, indent=2), encoding="utf-8")

    # Rollout state
    try:
        from workflow_dataset.rollout.tracker import load_rollout_state
        rollout = load_rollout_state(repo_root=root)
        summary["rollout_state"] = rollout
        (out / "rollout_state.json").write_text(json.dumps(rollout, indent=2), encoding="utf-8")
    except Exception as e:
        summary["rollout_state"] = {"error": str(e)}
        (out / "rollout_state.json").write_text(json.dumps({"error": str(e)}, indent=2), encoding="utf-8")

    # Copy/link last reports if present
    reports_dir = root / "data/local/acceptance/runs"
    if reports_dir.exists():
        for f in sorted(reports_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:3]:
            try:
                shutil.copy2(f, out / f"acceptance_run_{f.name}")
            except Exception:
                pass
    summary["report_paths"] = [str(p) for p in out.iterdir() if p.is_file()]

    # Issue summary template
    issue_text = format_issues_report(summary)
    (out / "issue_summary.txt").write_text(issue_text, encoding="utf-8")
    summary["issue_summary_path"] = str(out / "issue_summary.txt")

    return summary

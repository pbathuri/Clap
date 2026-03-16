"""
M23B-F5: Readiness check history — persist snapshots for drift detection.
Local-only; operator-started; no daemon.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.edge.checks import run_readiness_checks, checks_summary
from workflow_dataset.edge.profile import build_edge_profile
from workflow_dataset.utils.dates import utc_now_iso

EDGE_OUTPUT_DIR = "data/local/edge"
HISTORY_DIR = "history"
SNAPSHOT_PREFIX = "readiness_"
LATEST_FILENAME = "latest.json"


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root())
    except Exception:
        return Path.cwd().resolve()


def _history_dir(repo_root: Path) -> Path:
    d = repo_root / EDGE_OUTPUT_DIR / HISTORY_DIR
    d.mkdir(parents=True, exist_ok=True)
    return d


def snapshot_from_checks(
    checks: list[dict[str, Any]],
    summary: dict[str, Any],
    profile: dict[str, Any],
    timestamp_utc: str,
) -> dict[str, Any]:
    """Build a serializable snapshot for storage."""
    return {
        "timestamp_utc": timestamp_utc,
        "ready": summary.get("ready", False),
        "summary": {
            "passed": summary.get("passed", 0),
            "failed": summary.get("failed", 0),
            "failed_required": summary.get("failed_required", 0),
            "optional_disabled": summary.get("optional_disabled", 0),
        },
        "checks": [
            {"check_id": c.get("check_id"), "passed": c.get("passed"), "message": c.get("message"), "optional": c.get("optional")}
            for c in checks
        ],
        "supported_workflows": list(profile.get("supported_workflows") or []),
    }


def record_readiness_snapshot(
    repo_root: Path | str | None = None,
    config_path: str = "configs/settings.yaml",
) -> dict[str, Any]:
    """
    Run readiness checks, build snapshot, write to history/readiness_<timestamp>.json and history/latest.json.
    Returns the snapshot dict.
    """
    root = _repo_root(repo_root)
    hist_dir = _history_dir(root)
    timestamp_utc = utc_now_iso()
    # Use compact filename: readiness_YYYYMMDDTHHMMSS.json
    safe_ts = timestamp_utc.replace(":", "").replace("-", "")[:15]
    checks = run_readiness_checks(repo_root=root, config_path=config_path)
    summary = checks_summary(checks)
    profile = build_edge_profile(repo_root=root, config_path=config_path)
    snapshot = snapshot_from_checks(checks, summary, profile, timestamp_utc)

    path = hist_dir / f"{SNAPSHOT_PREFIX}{safe_ts}.json"
    path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    latest_path = hist_dir / LATEST_FILENAME
    latest_path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    snapshot["_path"] = str(path)
    snapshot["_latest_path"] = str(latest_path)
    return snapshot


def list_readiness_snapshots(
    repo_root: Path | str | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """List stored snapshots (path, timestamp_utc) newest first."""
    root = _repo_root(repo_root)
    hist_dir = _history_dir(root)
    out: list[dict[str, Any]] = []
    for p in sorted(hist_dir.glob(f"{SNAPSHOT_PREFIX}*.json"), key=lambda x: x.stat().st_mtime, reverse=True)[:limit]:
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            out.append({"path": str(p), "timestamp_utc": data.get("timestamp_utc", ""), "ready": data.get("ready")})
        except Exception:
            pass
    return out


def load_latest_snapshot(repo_root: Path | str | None = None) -> dict[str, Any] | None:
    """Load the most recently recorded snapshot (latest.json)."""
    root = _repo_root(repo_root)
    latest_path = root / EDGE_OUTPUT_DIR / HISTORY_DIR / LATEST_FILENAME
    if not latest_path.exists():
        return None
    try:
        return json.loads(latest_path.read_text(encoding="utf-8"))
    except Exception:
        return None


def load_previous_snapshot(repo_root: Path | str | None = None) -> dict[str, Any] | None:
    """Load the second-most-recent snapshot (for drift: current vs previous)."""
    listed = list_readiness_snapshots(repo_root=repo_root, limit=2)
    if len(listed) < 2:
        return None
    path = listed[1].get("path")
    if not path or not Path(path).exists():
        return None
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return None

"""
Run summary and success marker for training runs.

Enables: (1) writing run_summary.json on train/smoke-train completion,
(2) treating only successful runs as valid adapter sources for eval/demo.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_SUMMARY_FILENAME = "run_summary.json"


def write_run_summary(
    run_dir: Path,
    success: bool,
    *,
    backend: str = "",
    base_model: str = "",
    llm_config_path: str = "",
    adapter_path: str | Path | None = None,
    error: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    run_type: str = "full",
) -> Path:
    """
    Write run_summary.json into run_dir.
    success=True plus adapter_path indicates a run that produced a usable adapter.
    run_type: "smoke" | "full" for comparison and reporting.
    """
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    end = end_time or datetime.now(timezone.utc).isoformat()
    payload: dict[str, Any] = {
        "success": success,
        "run_type": run_type,
        "backend": backend,
        "base_model": base_model,
        "llm_config_path": llm_config_path,
        "start_time": start_time or "",
        "end_time": end,
        "adapter_path": str(adapter_path) if adapter_path else "",
        "error": error or "",
    }
    path = run_dir / RUN_SUMMARY_FILENAME
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return path


def is_successful_run(run_dir: Path) -> bool:
    """True if run_dir contains run_summary.json with success=true and adapter_path non-empty."""
    path = Path(run_dir) / RUN_SUMMARY_FILENAME
    if not path.exists():
        return False
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not data.get("success"):
            return False
        adapter = data.get("adapter_path", "")
        if not adapter:
            return False
        return Path(adapter).exists()
    except Exception:
        return False


def find_latest_successful_adapter(runs_dir: Path) -> tuple[str, str]:
    """
    Return (adapter_path, run_dir) for the most recent successful run, or ("", "").
    Only runs with run_summary.json success=true and existing adapter dir are considered.
    """
    candidates = _successful_runs_with_mtime(runs_dir)
    if not candidates:
        return "", ""
    candidates.sort(key=lambda x: x[2], reverse=True)
    return candidates[0][0], candidates[0][1]


def get_run_type(run_dir: Path) -> str:
    """Return run_type from run_summary.json, or infer from dir name: smoke_* -> smoke, else full."""
    path = Path(run_dir) / RUN_SUMMARY_FILENAME
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("run_type", "full")
        except Exception:
            pass
    return "smoke" if Path(run_dir).name.startswith("smoke_") else "full"


def find_latest_successful_adapter_by_type(
    runs_dir: Path, run_type: str
) -> tuple[str, str]:
    """Return (adapter_path, run_dir) for the most recent successful run of given run_type (smoke | full)."""
    candidates = _successful_runs_with_mtime(runs_dir)
    filtered = [(a, r, m) for a, r, m in candidates if get_run_type(Path(r)) == run_type]
    if not filtered:
        return "", ""
    filtered.sort(key=lambda x: x[2], reverse=True)
    return filtered[0][0], filtered[0][1]


def find_all_successful_adapters(runs_dir: Path) -> list[tuple[str, str]]:
    """Return [(adapter_path, run_dir), ...] for all successful runs, newest first."""
    candidates = _successful_runs_with_mtime(runs_dir)
    candidates.sort(key=lambda x: x[2], reverse=True)
    return [(a, r) for a, r, _ in candidates]


def _successful_runs_with_mtime(runs_dir: Path) -> list[tuple[str, str, float]]:
    """Return [(adapter_path, run_dir, mtime), ...] for successful runs."""
    if not runs_dir.exists():
        return []
    out: list[tuple[str, str, float]] = []
    for d in runs_dir.iterdir():
        if not d.is_dir():
            continue
        if not is_successful_run(d):
            continue
        adapters = d / "adapters"
        if not adapters.exists() or not any(adapters.iterdir()):
            continue
        try:
            m = d.stat().st_mtime
            out.append((str(adapters), str(d), m))
        except OSError:
            pass
    return out

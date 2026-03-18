"""
M42I–M42L: Benchmark board store — scorecards, comparisons, promotion/rollback history.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DIR_NAME = "data/local/benchmark_board"
SCORECARDS_DIR = "scorecards"
COMPARISONS_DIR = "comparisons"
PROMOTION_HISTORY_FILE = "promotion_history.json"
ROLLBACK_HISTORY_FILE = "rollback_history.json"
QUARANTINE_FILE = "quarantined.json"
PROMOTED_FILE = "promoted.json"
SHADOW_RUNS_FILE = "shadow_runs.json"


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def get_benchmark_board_dir(repo_root: Path | str | None = None) -> Path:
    return _repo_root(repo_root) / DIR_NAME


def save_scorecard(scorecard: dict[str, Any], repo_root: Path | str | None = None) -> Path:
    root = _repo_root(repo_root)
    d = root / DIR_NAME / SCORECARDS_DIR
    d.mkdir(parents=True, exist_ok=True)
    sid = scorecard.get("scorecard_id", "sc_unknown")
    path = d / f"{sid}.json"
    path.write_text(json.dumps(scorecard, indent=2), encoding="utf-8")
    return path


def load_scorecard(scorecard_id: str, repo_root: Path | str | None = None) -> dict[str, Any] | None:
    root = _repo_root(repo_root)
    path = root / DIR_NAME / SCORECARDS_DIR / f"{scorecard_id}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def list_scorecards(limit: int = 50, repo_root: Path | str | None = None) -> list[dict[str, Any]]:
    root = _repo_root(repo_root)
    d = root / DIR_NAME / SCORECARDS_DIR
    if not d.exists():
        return []
    out: list[dict[str, Any]] = []
    for p in sorted(d.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            out.append(json.loads(p.read_text(encoding="utf-8")))
            if len(out) >= limit:
                break
        except Exception:
            pass
    return out


def append_promotion_decision(
    candidate_id: str,
    decision: str,
    scope: str = "",
    reason: str = "",
    scorecard_id: str = "",
    repo_root: Path | str | None = None,
) -> None:
    root = _repo_root(repo_root)
    d = root / DIR_NAME
    d.mkdir(parents=True, exist_ok=True)
    path = d / PROMOTION_HISTORY_FILE
    history: list[dict[str, Any]] = []
    if path.exists():
        try:
            history = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            history = []
    history.append({
        "candidate_id": candidate_id,
        "decision": decision,
        "scope": scope,
        "reason": reason,
        "scorecard_id": scorecard_id,
    })
    if len(history) > 500:
        history = history[-500:]
    path.write_text(json.dumps(history, indent=2), encoding="utf-8")


def append_rollback(candidate_id: str, prior_id: str, reason: str = "", repo_root: Path | str | None = None) -> None:
    root = _repo_root(repo_root)
    d = root / DIR_NAME
    d.mkdir(parents=True, exist_ok=True)
    path = d / ROLLBACK_HISTORY_FILE
    history: list[dict[str, Any]] = []
    if path.exists():
        try:
            history = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            history = []
    history.append({"candidate_id": candidate_id, "prior_id": prior_id, "reason": reason})
    if len(history) > 200:
        history = history[-200:]
    path.write_text(json.dumps(history, indent=2), encoding="utf-8")


def set_quarantined(candidate_ids: list[str], repo_root: Path | str | None = None) -> None:
    root = _repo_root(repo_root)
    d = root / DIR_NAME
    d.mkdir(parents=True, exist_ok=True)
    path = d / QUARANTINE_FILE
    path.write_text(json.dumps({"candidate_ids": list(candidate_ids)}, indent=2), encoding="utf-8")


def get_quarantined(repo_root: Path | str | None = None) -> list[str]:
    root = _repo_root(repo_root)
    path = root / DIR_NAME / QUARANTINE_FILE
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return list(data.get("candidate_ids", []))
    except Exception:
        return []


def add_quarantined(candidate_id: str, repo_root: Path | str | None = None) -> None:
    cur = get_quarantined(repo_root=repo_root)
    if candidate_id not in cur:
        cur.append(candidate_id)
        set_quarantined(cur, repo_root=repo_root)


def remove_quarantined(candidate_id: str, repo_root: Path | str | None = None) -> None:
    cur = get_quarantined(repo_root=repo_root)
    if candidate_id in cur:
        cur.remove(candidate_id)
        set_quarantined(cur, repo_root=repo_root)


def set_promoted(candidate_id: str, scope: str, repo_root: Path | str | None = None) -> None:
    root = _repo_root(repo_root)
    d = root / DIR_NAME
    d.mkdir(parents=True, exist_ok=True)
    path = d / PROMOTED_FILE
    data: dict[str, Any] = {}
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    data["latest_promoted_id"] = candidate_id
    data["latest_promoted_scope"] = scope
    data["history"] = data.get("history", [])
    data["history"].append({"candidate_id": candidate_id, "scope": scope})
    if len(data["history"]) > 100:
        data["history"] = data["history"][-100:]
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def get_latest_promoted(repo_root: Path | str | None = None) -> tuple[str, str]:
    root = _repo_root(repo_root)
    path = root / DIR_NAME / PROMOTED_FILE
    if not path.exists():
        return "", ""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("latest_promoted_id", ""), data.get("latest_promoted_scope", "")
    except Exception:
        return "", ""


def list_promotion_history(limit: int = 20, repo_root: Path | str | None = None) -> list[dict[str, Any]]:
    root = _repo_root(repo_root)
    path = root / DIR_NAME / PROMOTION_HISTORY_FILE
    if not path.exists():
        return []
    try:
        history = json.loads(path.read_text(encoding="utf-8"))
        return list(reversed(history[-limit:]))
    except Exception:
        return []


def list_rollback_history(limit: int = 20, repo_root: Path | str | None = None) -> list[dict[str, Any]]:
    root = _repo_root(repo_root)
    path = root / DIR_NAME / ROLLBACK_HISTORY_FILE
    if not path.exists():
        return []
    try:
        history = json.loads(path.read_text(encoding="utf-8"))
        return list(reversed(history[-limit:]))
    except Exception:
        return []


# --- M42L.1 Shadow-mode runs ---


def append_shadow_run(
    candidate_id: str,
    production_run_id: str,
    candidate_run_id: str,
    slice_id: str = "",
    production_score: float = 0.0,
    candidate_score: float = 0.0,
    outcome: str = "",  # match | candidate_better | production_better | disagree
    at_iso: str = "",
    repo_root: Path | str | None = None,
) -> None:
    root = _repo_root(repo_root)
    d = root / DIR_NAME
    d.mkdir(parents=True, exist_ok=True)
    path = d / SHADOW_RUNS_FILE
    runs: list[dict[str, Any]] = []
    if path.exists():
        try:
            runs = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            runs = []
    runs.append({
        "candidate_id": candidate_id,
        "production_run_id": production_run_id,
        "candidate_run_id": candidate_run_id,
        "slice_id": slice_id,
        "production_score": production_score,
        "candidate_score": candidate_score,
        "outcome": outcome,
        "at_iso": at_iso,
    })
    if len(runs) > 500:
        runs = runs[-500:]
    path.write_text(json.dumps(runs, indent=2), encoding="utf-8")


def list_shadow_runs(
    candidate_id: str | None = None,
    limit: int = 50,
    repo_root: Path | str | None = None,
) -> list[dict[str, Any]]:
    root = _repo_root(repo_root)
    path = root / DIR_NAME / SHADOW_RUNS_FILE
    if not path.exists():
        return []
    try:
        runs = json.loads(path.read_text(encoding="utf-8"))
        if candidate_id:
            runs = [r for r in runs if r.get("candidate_id") == candidate_id]
        return list(reversed(runs[-limit:]))
    except Exception:
        return []

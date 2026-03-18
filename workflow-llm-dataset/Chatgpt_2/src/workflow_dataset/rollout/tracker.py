"""
M24F: Rollout tracker — target scenario, stage, passed checks, blocked items,
support notes, next action, latest acceptance result. Persisted under data/local/rollout/.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

ROLLOUT_DIR = "data/local/rollout"
STATE_FILE = "rollout_state.json"


def _repo_root(root: Path | str | None) -> Path:
    if root is not None:
        return Path(root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def get_rollout_dir(repo_root: Path | str | None = None) -> Path:
    return _repo_root(repo_root) / ROLLOUT_DIR


def get_state_path(repo_root: Path | str | None = None) -> Path:
    return get_rollout_dir(repo_root) / STATE_FILE


def load_rollout_state(repo_root: Path | str | None = None) -> dict[str, Any]:
    """Load rollout state from data/local/rollout/rollout_state.json. Returns empty dict if missing."""
    path = get_state_path(repo_root)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_rollout_state(state: dict[str, Any], repo_root: Path | str | None = None) -> Path:
    """Write rollout state to data/local/rollout/rollout_state.json."""
    root = _repo_root(repo_root)
    path = get_state_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    state["updated_at"] = utc_now_iso()
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")
    return path


def update_rollout_from_acceptance(
    acceptance_result: dict[str, Any],
    repo_root: Path | str | None = None,
    target_scenario_id: str | None = None,
) -> dict[str, Any]:
    """
    Update rollout state from a run_scenario result. Sets target_scenario_id, current_stage,
    passed_checks, blocked_items, latest_acceptance_result, next_required_action.
    """
    state = load_rollout_state(repo_root)
    scenario_id = acceptance_result.get("scenario_id") or target_scenario_id
    outcome = acceptance_result.get("outcome", "fail")
    reasons = acceptance_result.get("reasons", [])
    ready = acceptance_result.get("ready_for_trial", False)

    state["target_scenario_id"] = scenario_id or state.get("target_scenario_id")
    state["current_stage"] = "ready_for_trial" if ready else ("blocked" if outcome == "blocked" else "in_progress")
    state["passed_readiness_checks"] = state.get("passed_readiness_checks", [])
    if outcome == "pass" and "acceptance_pass" not in state.get("passed_readiness_checks", []):
        state["passed_readiness_checks"] = list(set(state["passed_readiness_checks"] + ["acceptance_pass"]))
    state["blocked_items"] = reasons if outcome == "blocked" else state.get("blocked_items", [])
    if outcome == "fail":
        state["blocked_items"] = list(set(state.get("blocked_items", []) + reasons))
    state["latest_acceptance_result"] = {
        "scenario_id": scenario_id,
        "outcome": outcome,
        "reasons": reasons,
        "ready_for_trial": ready,
    }
    if outcome == "pass":
        state["next_required_action"] = "Proceed to first real user / pilot; run inbox and first-value flow as needed."
    elif outcome == "blocked":
        state["next_required_action"] = "Fix blocked items (install, kit prerequisites); re-run acceptance."
    else:
        state["next_required_action"] = "Address reasons; re-run acceptance run --id " + (scenario_id or "SCENARIO")

    save_rollout_state(state, repo_root)
    return state

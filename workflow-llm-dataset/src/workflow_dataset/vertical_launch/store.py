"""
M39I–M39L: Persist active launch kit, launch start time, setup checklist state, success proof state.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

LAUNCH_DIR = "data/local/vertical_launch"
ACTIVE_FILE = "active.json"
PROOF_FILE = "proof_state.json"
ROLLOUT_DECISIONS_FILE = "rollout_decisions.jsonl"


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _launch_dir(repo_root: Path | str | None) -> Path:
    return _root(repo_root) / LAUNCH_DIR


def get_active_launch(repo_root: Path | str | None = None) -> dict[str, Any]:
    """Return active launch state: active_launch_kit_id, launch_started_at_utc, curated_pack_id."""
    path = _launch_dir(repo_root) / ACTIVE_FILE
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def set_active_launch(
    launch_kit_id: str,
    curated_pack_id: str = "",
    repo_root: Path | str | None = None,
) -> Path:
    """Set active launch kit and record launch_started_at_utc."""
    from datetime import datetime, timezone
    root = _launch_dir(repo_root)
    root.mkdir(parents=True, exist_ok=True)
    path = root / ACTIVE_FILE
    data = {
        "active_launch_kit_id": launch_kit_id,
        "curated_pack_id": curated_pack_id,
        "launch_started_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def clear_active_launch(repo_root: Path | str | None = None) -> bool:
    path = _launch_dir(repo_root) / ACTIVE_FILE
    if path.exists():
        path.unlink()
        return True
    return False


def get_proof_state(repo_root: Path | str | None = None) -> dict[str, Any]:
    """Return proof state: launch_kit_id, proofs[{proof_id, status, reached_at_utc}], updated_at_utc."""
    path = _launch_dir(repo_root) / PROOF_FILE
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def set_proof_state(
    launch_kit_id: str,
    proofs: list[dict[str, Any]],
    repo_root: Path | str | None = None,
) -> Path:
    """Persist proof state for the active launch kit."""
    from datetime import datetime, timezone
    root = _launch_dir(repo_root)
    root.mkdir(parents=True, exist_ok=True)
    path = root / PROOF_FILE
    data = {
        "launch_kit_id": launch_kit_id,
        "proofs": proofs,
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def record_proof_met(
    proof_id: str,
    launch_kit_id: str = "",
    repo_root: Path | str | None = None,
) -> bool:
    """Mark one proof as met; append to proof state if not already present."""
    from datetime import datetime, timezone
    state = get_proof_state(repo_root)
    kit = launch_kit_id or state.get("launch_kit_id", "")
    proofs = list(state.get("proofs", []))
    now = datetime.now(timezone.utc).isoformat()
    for p in proofs:
        if p.get("proof_id") == proof_id:
            p["status"] = "met"
            p["reached_at_utc"] = now
            set_proof_state(kit, proofs, repo_root)
            return True
    proofs.append({"proof_id": proof_id, "status": "met", "reached_at_utc": now})
    set_proof_state(kit, proofs, repo_root)
    return True


def _rollout_decisions_path(repo_root: Path | str | None) -> Path:
    return _launch_dir(repo_root) / ROLLOUT_DECISIONS_FILE


def save_rollout_decision(
    vertical_id: str,
    launch_kit_id: str,
    decision: str,
    rationale: str = "",
    recorded_by: str = "cli",
    repo_root: Path | str | None = None,
) -> Path:
    """Append one rollout decision (JSONL)."""
    from datetime import datetime, timezone
    try:
        from workflow_dataset.utils.hashes import stable_id
    except Exception:
        def stable_id(*parts: str, prefix: str = "") -> str:
            import hashlib
            return prefix + hashlib.sha256("".join(str(p) for p in parts).encode()).hexdigest()[:12]
    root = _launch_dir(repo_root)
    root.mkdir(parents=True, exist_ok=True)
    path = _rollout_decisions_path(repo_root)
    now = datetime.now(timezone.utc).isoformat()
    decision_id = stable_id("rollout", vertical_id, decision, now, prefix="rollout_")
    record = {
        "decision_id": decision_id,
        "vertical_id": vertical_id,
        "launch_kit_id": launch_kit_id,
        "decision": decision,
        "rationale": rationale,
        "recorded_at_utc": now,
        "recorded_by": recorded_by,
    }
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    return path


def list_rollout_decisions(
    vertical_id: str = "",
    launch_kit_id: str = "",
    limit: int = 20,
    repo_root: Path | str | None = None,
) -> list[dict[str, Any]]:
    """List recent rollout decisions (newest last in file). Optional filter by vertical_id or launch_kit_id."""
    path = _rollout_decisions_path(repo_root)
    if not path.exists():
        return []
    lines: list[str] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                lines.append(line)
    out: list[dict[str, Any]] = []
    for line in reversed(lines[-limit * 2:]):
        try:
            d = json.loads(line)
            if vertical_id and d.get("vertical_id") != vertical_id:
                continue
            if launch_kit_id and d.get("launch_kit_id") != launch_kit_id:
                continue
            out.append(d)
            if len(out) >= limit:
                break
        except Exception:
            continue
    return out

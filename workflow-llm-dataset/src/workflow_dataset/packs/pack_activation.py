"""
M24: Activation state — primary pack, secondary, pinned, suspended. Stored in activation_state.json.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.packs.pack_state import get_packs_dir, _default_packs_dir


def _activation_path(packs_dir: Path | str | None = None) -> Path:
    root = Path(packs_dir) if packs_dir else _default_packs_dir()
    root.mkdir(parents=True, exist_ok=True)
    return root / "activation_state.json"


def load_activation_state(packs_dir: Path | str | None = None) -> dict[str, Any]:
    """Load activation state. Keys: primary_pack_id, secondary_pack_ids, pinned, suspended_pack_ids, current_role, current_workflow, current_task."""
    path = _activation_path(packs_dir)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_activation_state(state: dict[str, Any], packs_dir: Path | str | None = None) -> Path:
    """Save activation state."""
    path = _activation_path(packs_dir)
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")
    return path


def get_primary_pack_id(packs_dir: Path | str | None = None) -> str:
    """Return primary role pack id or empty."""
    return (load_activation_state(packs_dir).get("primary_pack_id") or "").strip()


def set_primary_pack(pack_id: str, packs_dir: Path | str | None = None) -> Path:
    """Set primary pack. Also sets current_role from pack's role_tags if loadable."""
    state = load_activation_state(packs_dir)
    state["primary_pack_id"] = pack_id.strip()
    try:
        from workflow_dataset.packs.pack_registry import get_installed_manifest
        m = get_installed_manifest(pack_id, packs_dir)
        if m and m.role_tags:
            state["current_role"] = m.role_tags[0]
    except Exception:
        pass
    return save_activation_state(state, packs_dir)


def clear_primary_pack(packs_dir: Path | str | None = None) -> Path:
    """Clear primary pack (and current_role in state)."""
    state = load_activation_state(packs_dir)
    state.pop("primary_pack_id", None)
    state.pop("current_role", None)
    return save_activation_state(state, packs_dir)


def get_secondary_pack_ids(packs_dir: Path | str | None = None) -> list[str]:
    """Return list of secondary pack ids."""
    raw = load_activation_state(packs_dir).get("secondary_pack_ids") or []
    return [x for x in raw if isinstance(x, str) and x.strip()]


def add_secondary_pack(pack_id: str, packs_dir: Path | str | None = None) -> Path:
    """Add pack to secondary list if not present."""
    state = load_activation_state(packs_dir)
    sec = state.get("secondary_pack_ids") or []
    if not isinstance(sec, list):
        sec = []
    pack_id = pack_id.strip()
    if pack_id not in sec:
        sec.append(pack_id)
    state["secondary_pack_ids"] = sec
    return save_activation_state(state, packs_dir)


def remove_secondary_pack(pack_id: str, packs_dir: Path | str | None = None) -> Path:
    """Remove pack from secondary list."""
    state = load_activation_state(packs_dir)
    sec = [x for x in (state.get("secondary_pack_ids") or []) if x != pack_id.strip()]
    state["secondary_pack_ids"] = sec
    return save_activation_state(state, packs_dir)


def get_pinned(packs_dir: Path | str | None = None) -> dict[str, str]:
    """Return pinned map: scope -> pack_id. Scope is session, project, or task."""
    raw = load_activation_state(packs_dir).get("pinned") or {}
    return {k: v for k, v in raw.items() if isinstance(v, str) and v.strip()} if isinstance(raw, dict) else {}


def pin_pack(pack_id: str, scope: str, packs_dir: Path | str | None = None) -> Path:
    """Pin pack for scope (session, project, task)."""
    state = load_activation_state(packs_dir)
    pinned = dict(state.get("pinned") or {})
    pinned[scope.strip()] = pack_id.strip()
    state["pinned"] = pinned
    return save_activation_state(state, packs_dir)


def unpin_pack(pack_id: str | None, scope: str | None, packs_dir: Path | str | None = None) -> Path:
    """Unpin: if scope given remove that scope; if pack_id given remove all pins for that pack."""
    state = load_activation_state(packs_dir)
    pinned = dict(state.get("pinned") or {})
    if scope is not None:
        pinned.pop(scope.strip(), None)
    if pack_id is not None:
        pack_id = pack_id.strip()
        pinned = {k: v for k, v in pinned.items() if v != pack_id}
    state["pinned"] = pinned
    return save_activation_state(state, packs_dir)


def get_suspended_pack_ids(packs_dir: Path | str | None = None) -> list[str]:
    """Return list of suspended pack ids."""
    raw = load_activation_state(packs_dir).get("suspended_pack_ids") or []
    return [x for x in raw if isinstance(x, str) and x.strip()]


def suspend_pack(pack_id: str, packs_dir: Path | str | None = None) -> Path:
    """Suspend pack (exclude from resolution)."""
    state = load_activation_state(packs_dir)
    sus = list(state.get("suspended_pack_ids") or [])
    pack_id = pack_id.strip()
    if pack_id not in sus:
        sus.append(pack_id)
    state["suspended_pack_ids"] = sus
    return save_activation_state(state, packs_dir)


def resume_pack(pack_id: str, packs_dir: Path | str | None = None) -> Path:
    """Resume pack (include in resolution again)."""
    state = load_activation_state(packs_dir)
    sus = [x for x in (state.get("suspended_pack_ids") or []) if x != pack_id.strip()]
    state["suspended_pack_ids"] = sus
    return save_activation_state(state, packs_dir)


def get_current_context(packs_dir: Path | str | None = None) -> dict[str, str]:
    """Return current_role, current_workflow, current_task."""
    state = load_activation_state(packs_dir)
    return {
        "current_role": (state.get("current_role") or "").strip(),
        "current_workflow": (state.get("current_workflow") or "").strip(),
        "current_task": (state.get("current_task") or "").strip(),
    }


def set_current_role(role: str, packs_dir: Path | str | None = None) -> Path:
    """Set current role in activation state."""
    state = load_activation_state(packs_dir)
    state["current_role"] = role.strip()
    return save_activation_state(state, packs_dir)


def set_current_context(workflow: str | None = None, task: str | None = None, packs_dir: Path | str | None = None) -> Path:
    """Set current_workflow and/or current_task."""
    state = load_activation_state(packs_dir)
    if workflow is not None:
        state["current_workflow"] = workflow.strip()
    if task is not None:
        state["current_task"] = task.strip()
    return save_activation_state(state, packs_dir)


def clear_context(packs_dir: Path | str | None = None) -> Path:
    """Clear current_role, current_workflow, current_task and all pins."""
    state = load_activation_state(packs_dir)
    state.pop("current_role", None)
    state.pop("current_workflow", None)
    state.pop("current_task", None)
    state["pinned"] = {}
    return save_activation_state(state, packs_dir)

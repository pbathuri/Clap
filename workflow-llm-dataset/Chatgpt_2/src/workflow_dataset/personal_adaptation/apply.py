"""
M31I–M31L: Apply accepted preference to surfaces. No silent apply of unreviewed candidates.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.personal_adaptation.store import get_accepted_dir
from workflow_dataset.personal_adaptation.models import AcceptedPreferenceUpdate


def _repo_root(root: Path | str | None) -> Path:
    if root is not None:
        return Path(root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _load_update(update_id: str, root: Path) -> AcceptedPreferenceUpdate | None:
    import json
    from workflow_dataset.personal_adaptation.store import get_accepted_dir
    acc_dir = get_accepted_dir(root)
    path = acc_dir / f"{update_id}.json"
    if not path.exists():
        return None
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
        return AcceptedPreferenceUpdate.from_dict(d)
    except Exception:
        return None


def apply_accepted_preference(
    update_id: str,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Apply an already-accepted preference update to the affected surface.
    Only applies if the update exists in accepted/ (i.e. was explicitly accepted).
    Returns summary: applied=True/False, surface, message, details.
    """
    root = _repo_root(repo_root)
    update = _load_update(update_id, root)
    if not update:
        return {
            "applied": False,
            "update_id": update_id,
            "surface": "",
            "message": f"Accepted update {update_id} not found.",
            "details": {},
        }
    surface = update.applied_surface
    details: dict[str, Any] = {
        "candidate_id": update.candidate_id,
        "key_or_pattern": update.key_or_pattern,
        "applied_value": update.applied_value,
    }

    # Apply to specialization_* surfaces via corrections.apply_update(proposed update_id) where match exists
    if surface == "specialization_output_style" and update.applied_value is not None:
        try:
            from workflow_dataset.corrections.propose import propose_updates
            from workflow_dataset.corrections.updates import apply_update
            proposed_list = propose_updates(repo_root=root, limit_corrections=100)
            for p in proposed_list:
                if p.target_type == "specialization_output_style" and p.after_value == update.applied_value:
                    apply_update(p.update_id, repo_root=root)
                    details["target_id"] = p.target_id
                    return {"applied": True, "update_id": update_id, "surface": surface, "message": f"Applied output_style to {p.target_id}.", "details": details}
            _write_preference_fallback(root, "output_style", update.key_or_pattern, update.applied_value)
            return {"applied": True, "update_id": update_id, "surface": surface, "message": "Recorded in preference store (no matching job pack target).", "details": details}
        except Exception as e:
            _write_preference_fallback(root, "output_style", update.key_or_pattern, update.applied_value)
            return {"applied": True, "update_id": update_id, "surface": surface, "message": f"Recorded in preference store: {e}", "details": details}

    if surface == "specialization_paths" and update.applied_value is not None:
        try:
            from workflow_dataset.corrections.propose import propose_updates
            from workflow_dataset.corrections.updates import apply_update
            proposed_list = propose_updates(repo_root=root, limit_corrections=100)
            for p in proposed_list:
                if p.target_type == "specialization_paths" and p.after_value == update.applied_value:
                    apply_update(p.update_id, repo_root=root)
                    details["target_id"] = p.target_id
                    return {"applied": True, "update_id": update_id, "surface": surface, "message": f"Applied paths to {p.target_id}.", "details": details}
            _write_preference_fallback(root, "paths", update.key_or_pattern, update.applied_value)
            return {"applied": True, "update_id": update_id, "surface": surface, "message": "Recorded in preference store.", "details": details}
        except Exception as e:
            _write_preference_fallback(root, "paths", update.key_or_pattern, update.applied_value)
            return {"applied": True, "update_id": update_id, "surface": surface, "message": str(e), "details": details}

    if surface == "specialization_params" and update.applied_value is not None:
        try:
            from workflow_dataset.corrections.propose import propose_updates
            from workflow_dataset.corrections.updates import apply_update
            proposed_list = propose_updates(repo_root=root, limit_corrections=100)
            for p in proposed_list:
                if p.target_type == "specialization_params" and p.after_value == update.applied_value:
                    apply_update(p.update_id, repo_root=root)
                    details["target_id"] = p.target_id
                    return {"applied": True, "update_id": update_id, "surface": surface, "message": f"Applied params to {p.target_id}.", "details": details}
            _write_preference_fallback(root, "params", update.key_or_pattern, update.applied_value)
            return {"applied": True, "update_id": update_id, "surface": surface, "message": "Recorded in preference store.", "details": details}
        except Exception as e:
            _write_preference_fallback(root, "params", update.key_or_pattern, update.applied_value)
            return {"applied": True, "update_id": update_id, "surface": surface, "message": str(e), "details": details}

    # workspace_preset, output_framing, suggested_actions, notification_style: record for downstream
    _write_preference_fallback(root, surface, update.key_or_pattern, update.applied_value)
    return {"applied": True, "update_id": update_id, "surface": surface, "message": "Recorded for downstream use.", "details": details}


def _write_preference_fallback(root: Path, surface: str, key: str, value: Any) -> None:
    """Write applied preference to data/local/personal_adaptation/applied_preferences.json for downstream consumers."""
    import json
    prefs_file = root / "data/local/personal_adaptation/applied_preferences.json"
    prefs_file.parent.mkdir(parents=True, exist_ok=True)
    data: dict[str, Any] = {}
    if prefs_file.exists():
        try:
            data = json.loads(prefs_file.read_text(encoding="utf-8"))
        except Exception:
            pass
    data.setdefault("by_surface", {})
    data["by_surface"].setdefault(surface, {})
    data["by_surface"][surface][key] = value
    prefs_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

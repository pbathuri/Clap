"""
M31L.1: Explicit before/after behavior deltas for safer review when applying learned preferences.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.personal_adaptation.models import BehaviorDelta
from workflow_dataset.personal_adaptation.store import get_candidate


def _repo_root(root: Path | str | None) -> Path:
    if root is not None:
        return Path(root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _read_applied_preferences(root: Path) -> dict[str, Any]:
    """Read current applied_preferences.json by_surface."""
    prefs_file = root / "data/local/personal_adaptation/applied_preferences.json"
    if not prefs_file.exists():
        return {}
    try:
        import json
        data = json.loads(prefs_file.read_text(encoding="utf-8"))
        return data.get("by_surface", {})
    except Exception:
        return {}


def _current_specialization_value(root: Path, surface: str, target_id: str) -> Any:
    """Current value for a specialization target (output_style, paths, params)."""
    try:
        if surface == "specialization_output_style":
            from workflow_dataset.job_packs import load_specialization
            spec = load_specialization(target_id, root)
            return getattr(spec, "preferred_output_style", None) if spec else None
        if surface == "specialization_paths":
            from workflow_dataset.job_packs import load_specialization
            spec = load_specialization(target_id, root)
            return list(getattr(spec, "preferred_paths", [])) if spec else []
        if surface == "specialization_params":
            from workflow_dataset.job_packs import load_specialization
            spec = load_specialization(target_id, root)
            return dict(getattr(spec, "preferred_params", {})) if spec else {}
    except Exception:
        pass
    return None


def build_behavior_delta_for_candidate(
    candidate_id: str,
    repo_root: Path | str | None = None,
) -> list[BehaviorDelta]:
    """
    Build explicit before/after deltas for applying this candidate (no apply).
    Returns list of BehaviorDelta for packs, workspace, recommendations as applicable.
    """
    root = _repo_root(repo_root)
    cand = get_candidate(candidate_id, root)
    if not cand:
        return []
    deltas: list[BehaviorDelta] = []
    surface = getattr(cand, "affected_surface", "")
    key_or_pattern = getattr(cand, "key", None) or getattr(cand, "pattern_type", "")
    after_value = getattr(cand, "proposed_value", None) or getattr(cand, "description", "")

    # Resolve target_id for specialization_* (e.g. key is "output_style.weekly_report" -> weekly_report)
    target_id = ""
    if surface.startswith("specialization_") and "." in str(key_or_pattern):
        target_id = str(key_or_pattern).split(".", 1)[-1]

    if surface == "specialization_output_style":
        before = _current_specialization_value(root, surface, target_id) if target_id else None
        if before is None:
            before = _read_applied_preferences(root).get("specialization_output_style", {}).get(key_or_pattern)
        human = f"Packs: output style for '{target_id or key_or_pattern}' will change from {repr(before)} to {repr(after_value)}."
        deltas.append(BehaviorDelta(surface=surface, key_or_target=target_id or key_or_pattern, before_value=before, after_value=after_value, human_summary=human))
    elif surface == "specialization_paths":
        before = _current_specialization_value(root, surface, target_id) if target_id else []
        if before is None or before == []:
            before = _read_applied_preferences(root).get("specialization_paths", {}).get(key_or_pattern)
        human = f"Packs: preferred paths for '{target_id or key_or_pattern}' will change to {repr(after_value)[:80]}."
        deltas.append(BehaviorDelta(surface=surface, key_or_target=target_id or key_or_pattern, before_value=before, after_value=after_value, human_summary=human))
    elif surface == "specialization_params":
        before = _current_specialization_value(root, surface, target_id) if target_id else {}
        if before is None:
            before = _read_applied_preferences(root).get("specialization_params", {}).get(key_or_pattern)
        human = f"Packs: preferred params for '{target_id or key_or_pattern}' will be updated."
        deltas.append(BehaviorDelta(surface=surface, key_or_target=target_id or key_or_pattern, before_value=before, after_value=after_value, human_summary=human))
    else:
        # workspace_preset, output_framing, suggested_actions, notification_style
        by_surface = _read_applied_preferences(root)
        before = by_surface.get(surface, {}).get(key_or_pattern)
        human = f"{surface.replace('_', ' ').title()}: '{key_or_pattern}' will be set to {repr(after_value)[:60]}."
        deltas.append(BehaviorDelta(surface=surface, key_or_target=key_or_pattern, before_value=before, after_value=after_value, human_summary=human))
    return deltas


def build_behavior_delta_for_preset(
    preset_id: str,
    repo_root: Path | str | None = None,
) -> list[BehaviorDelta]:
    """Build deltas for all candidates in a preset (combined list)."""
    from workflow_dataset.personal_adaptation.presets import load_preset
    root = _repo_root(repo_root)
    preset = load_preset(preset_id, root)
    if not preset:
        return []
    out: list[BehaviorDelta] = []
    for cid in preset.candidate_ids:
        out.extend(build_behavior_delta_for_candidate(cid, root))
    return out


def format_behavior_delta_output(deltas: list[BehaviorDelta], candidate_id: str = "") -> str:
    """Format deltas as human-readable review text."""
    lines = ["# Behavior delta (before → after)", ""]
    if candidate_id:
        lines.append(f"Candidate: {candidate_id}")
        lines.append("")
    for d in deltas:
        lines.append(f"## {d.surface}")
        lines.append(f"  Key/target: {d.key_or_target}")
        lines.append(f"  Before: {repr(d.before_value)}")
        lines.append(f"  After:  {repr(d.after_value)}")
        lines.append(f"  → {d.human_summary}")
        lines.append("")
    return "\n".join(lines).strip()

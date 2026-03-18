"""
M47L.1: Guidance presets — concise, operator-first, review-heavy; load/save and apply to guidance output.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.quality_guidance.models import GuidancePreset, GuidancePresetKind, GuidanceItem


DEFAULT_PRESETS: list[GuidancePreset] = [
    GuidancePreset(
        preset_id="concise",
        kind=GuidancePresetKind.CONCISE.value,
        label="Concise",
        max_rationale_chars=120,
        emphasize_commands=True,
        emphasize_review=False,
        lead_with_recommendation=True,
        description="Short rationale; lead with recommendation; emphasize commands.",
    ),
    GuidancePreset(
        preset_id="operator_first",
        kind=GuidancePresetKind.OPERATOR_FIRST.value,
        label="Operator-first",
        max_rationale_chars=0,
        emphasize_commands=True,
        emphasize_review=False,
        lead_with_recommendation=True,
        description="Clear next step and command first; then context.",
    ),
    GuidancePreset(
        preset_id="review_heavy",
        kind=GuidancePresetKind.REVIEW_HEAVY.value,
        label="Review-heavy",
        max_rationale_chars=0,
        emphasize_commands=True,
        emphasize_review=True,
        lead_with_recommendation=False,
        description="Emphasize review backlog and what needs operator attention.",
    ),
]


def get_default_presets() -> list[GuidancePreset]:
    return list(DEFAULT_PRESETS)


def get_preset_for(preset_id: str) -> GuidancePreset | None:
    for p in DEFAULT_PRESETS:
        if p.preset_id == preset_id:
            return p
    return None


def load_active_preset(repo_root: Path | str | None = None) -> GuidancePreset:
    root = _repo_root(repo_root)
    path = root / "data/local/quality_guidance/preset.json"
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            pid = data.get("preset_id", "operator_first")
            p = get_preset_for(pid)
            if p:
                return p
        except Exception:
            pass
    return get_preset_for("operator_first") or DEFAULT_PRESETS[1]


def save_active_preset(preset_id: str, repo_root: Path | str | None = None) -> Path:
    root = _repo_root(repo_root)
    d = root / "data/local/quality_guidance"
    d.mkdir(parents=True, exist_ok=True)
    path = d / "preset.json"
    path.write_text(
        json.dumps({"preset_id": preset_id}, indent=2),
        encoding="utf-8",
    )
    return path


def apply_preset_to_guidance(
    item: GuidanceItem,
    preset: GuidancePreset,
) -> tuple[str, str]:
    """
    Return (summary, rationale) formatted per preset. Does not mutate item.
    """
    summary = item.summary
    rationale = item.rationale
    if preset.max_rationale_chars > 0 and len(rationale) > preset.max_rationale_chars:
        rationale = rationale[: preset.max_rationale_chars].rsplit(" ", 1)[0] + "…"
    if preset.lead_with_recommendation and item.action_ref:
        if preset.emphasize_commands:
            summary = f"{summary} → {item.action_ref[:80]}"
    if preset.emphasize_review and item.quality_signal.needs_review:
        nr = item.quality_signal.needs_review
        rationale = f"[Review: {nr.label}] {rationale}"
    return summary, rationale


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()

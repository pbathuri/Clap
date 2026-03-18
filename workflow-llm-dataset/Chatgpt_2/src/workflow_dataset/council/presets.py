"""
M41H.1: Council presets — conservative production, balanced improvement, research mode.
"""

from __future__ import annotations

from workflow_dataset.council.models import (
    CouncilPreset,
    PRESET_CONSERVATIVE_PRODUCTION,
    PRESET_BALANCED_IMPROVEMENT,
    PRESET_RESEARCH_MODE,
    DEFAULT_PRESET_ID,
    PERSPECTIVE_SAFETY_TRUST,
    PERSPECTIVE_ADAPTATION_RISK,
)


def _conservative_production() -> CouncilPreset:
    return CouncilPreset(
        preset_id=PRESET_CONSERVATIVE_PRODUCTION,
        label="Conservative production",
        description="Strict thresholds for production; prefer quarantine over limited rollout when uncertain.",
        min_score_to_promote=0.75,
        min_evidence_to_promote=3,
        required_perspectives_pass=[PERSPECTIVE_SAFETY_TRUST, PERSPECTIVE_ADAPTATION_RISK],
        allow_limited_rollout=True,
        allow_safe_experimental_only=True,
        reject_if_safety_below=0.5,
        quarantine_if_adaptation_risk_below=0.5,
        quarantine_if_any_high_severity_disagreement=True,
        needs_evidence_if_low_evidence=True,
    )


def _balanced_improvement() -> CouncilPreset:
    return CouncilPreset(
        preset_id=PRESET_BALANCED_IMPROVEMENT,
        label="Balanced improvement",
        description="Default: allow limited rollout and safe experimental when criteria met; quarantine on high-risk.",
        min_score_to_promote=0.6,
        min_evidence_to_promote=2,
        required_perspectives_pass=[],
        allow_limited_rollout=True,
        allow_safe_experimental_only=True,
        reject_if_safety_below=0.4,
        quarantine_if_adaptation_risk_below=0.4,
        quarantine_if_any_high_severity_disagreement=True,
        needs_evidence_if_low_evidence=True,
    )


def _research_mode() -> CouncilPreset:
    return CouncilPreset(
        preset_id=PRESET_RESEARCH_MODE,
        label="Research mode",
        description="Relaxed for experiments; allow safe_experimental and limited with lower evidence; still reject on safety.",
        min_score_to_promote=0.5,
        min_evidence_to_promote=1,
        required_perspectives_pass=[PERSPECTIVE_SAFETY_TRUST],
        allow_limited_rollout=True,
        allow_safe_experimental_only=True,
        reject_if_safety_below=0.35,
        quarantine_if_adaptation_risk_below=0.3,
        quarantine_if_any_high_severity_disagreement=False,
        needs_evidence_if_low_evidence=False,
    )


PRESETS: dict[str, CouncilPreset] = {
    PRESET_CONSERVATIVE_PRODUCTION: _conservative_production(),
    PRESET_BALANCED_IMPROVEMENT: _balanced_improvement(),
    PRESET_RESEARCH_MODE: _research_mode(),
}


def get_preset(preset_id: str) -> CouncilPreset | None:
    """Return council preset by id, or None."""
    return PRESETS.get(preset_id)


def list_presets() -> list[CouncilPreset]:
    """Return all presets in stable order."""
    return [
        PRESETS[PRESET_CONSERVATIVE_PRODUCTION],
        PRESETS[PRESET_BALANCED_IMPROVEMENT],
        PRESETS[PRESET_RESEARCH_MODE],
    ]


def get_default_preset() -> CouncilPreset:
    """Return default preset (balanced_improvement)."""
    return PRESETS[DEFAULT_PRESET_ID]

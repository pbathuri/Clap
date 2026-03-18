"""
M49L.1: Post-restore operating presets — how to run safely after migration.
"""

from __future__ import annotations

from workflow_dataset.continuity_confidence.models import (
    PostRestoreOperatingPreset,
    DeviceClass,
    ContinuityConfidenceClass,
)
from workflow_dataset.continuity_confidence.device_classes import get_device_class, list_device_classes


def _builtin_presets() -> list[PostRestoreOperatingPreset]:
    return [
        PostRestoreOperatingPreset(
            preset_id="full_operation",
            label="Full operation",
            description="Run as normal after migration; operator mode and production cut as configured after optional review.",
            recommended_routing_policy_id="balanced",
            production_cut_narrowed=False,
            operator_mode_trusted=True,
            require_review_before_production=False,
            do_after_migration=[
                "Run continuity-confidence report once to confirm state.",
                "Use operator mode and production cut as configured.",
            ],
            avoid_after_migration=[],
            next_review_action="Optional: workflow-dataset continuity-confidence report",
            when_to_use="Use when device class is full_local_workstation and confidence is high_confidence.",
        ),
        PostRestoreOperatingPreset(
            preset_id="review_before_production",
            label="Review before production",
            description="Run with narrowed production cut; complete review before enabling operator mode or full production.",
            recommended_routing_policy_id="conservative",
            production_cut_narrowed=True,
            operator_mode_trusted=False,
            require_review_before_production=True,
            do_after_migration=[
                "Run workflow-dataset continuity-confidence report.",
                "Narrow production cut until review is complete.",
                "Run continuity-confidence explain to see downgraded capabilities.",
            ],
            avoid_after_migration=[
                "Do not enable operator mode until review is complete.",
                "Do not assume all backends or features are available.",
            ],
            next_review_action="workflow-dataset continuity-confidence report",
            when_to_use="Use when confidence is review_required or usable_degraded, or device is constrained_laptop.",
        ),
        PostRestoreOperatingPreset(
            preset_id="recovery_safe",
            label="Recovery-safe",
            description="Minimal safe operation after migration; no operator mode, no real execution until environment is upgraded.",
            recommended_routing_policy_id="conservative",
            production_cut_narrowed=True,
            operator_mode_trusted=False,
            require_review_before_production=True,
            do_after_migration=[
                "Run continuity-confidence report and explain.",
                "Use suggestion-only or read-only workflows until backends are available.",
                "Upgrade device or install backends before enabling operator mode.",
            ],
            avoid_after_migration=[
                "Do not enable operator mode.",
                "Do not run real execution or production cut without review.",
                "Do not assume LLM or full backends are available.",
            ],
            next_review_action="workflow-dataset continuity-confidence explain",
            when_to_use="Use when device class is recovery_safe_environment or confidence is operator_mode_not_trusted or blocked.",
        ),
        PostRestoreOperatingPreset(
            preset_id="constrained",
            label="Constrained",
            description="Run with constrained routing and narrowed production cut; operator mode only after explicit review.",
            recommended_routing_policy_id="conservative",
            production_cut_narrowed=True,
            operator_mode_trusted=False,
            require_review_before_production=True,
            do_after_migration=[
                "Run continuity-confidence device-profile to confirm device class.",
                "Run continuity-confidence report and follow recommended posture.",
                "Use conservative routing policy until review is complete.",
            ],
            avoid_after_migration=[
                "Do not enable operator mode without running continuity-confidence report first.",
                "Do not assume full backends; use degraded fallback if needed.",
            ],
            next_review_action="workflow-dataset continuity-confidence report",
            when_to_use="Use when device class is constrained_laptop or confidence is narrowed_production_cut.",
        ),
    ]


_PRESETS: list[PostRestoreOperatingPreset] | None = None


def list_post_restore_presets() -> list[PostRestoreOperatingPreset]:
    """Return all built-in post-restore operating presets."""
    global _PRESETS
    if _PRESETS is None:
        _PRESETS = _builtin_presets()
    return list(_PRESETS)


def get_post_restore_preset(preset_id: str) -> PostRestoreOperatingPreset | None:
    """Return the preset with the given preset_id, or None."""
    for p in list_post_restore_presets():
        if p.preset_id == preset_id:
            return p
    return None


def get_recommended_preset_for(
    device_class_id: str = "",
    confidence_class: str = "",
) -> PostRestoreOperatingPreset:
    """
    Return the recommended post-restore preset for the given device class and continuity confidence class.
    """
    presets = list_post_restore_presets()
    confidence = (confidence_class or "").strip().lower()
    device = (device_class_id or "").strip().lower()

    if confidence in (ContinuityConfidenceClass.BLOCKED.value, ContinuityConfidenceClass.OPERATOR_MODE_NOT_TRUSTED.value):
        p = get_post_restore_preset("recovery_safe")
        if p:
            return p
    if "recovery_safe" in device or "recovery_safe_environment" in device:
        p = get_post_restore_preset("recovery_safe")
        if p:
            return p
    if "constrained" in device or "constrained_laptop" in device:
        p = get_post_restore_preset("constrained")
        if p:
            return p
    if confidence in (
        ContinuityConfidenceClass.REVIEW_REQUIRED.value,
        ContinuityConfidenceClass.USABLE_DEGRADED.value,
        ContinuityConfidenceClass.NARROWED_PRODUCTION_CUT.value,
    ):
        p = get_post_restore_preset("review_before_production")
        if p:
            return p
    if confidence == ContinuityConfidenceClass.HIGH_CONFIDENCE.value and "full_local" in device:
        p = get_post_restore_preset("full_operation")
        if p:
            return p

    return presets[1] if len(presets) > 1 else presets[0]

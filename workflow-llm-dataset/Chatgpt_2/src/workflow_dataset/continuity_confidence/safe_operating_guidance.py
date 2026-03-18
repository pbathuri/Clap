"""
M49L.1: Post-restore safe operating guidance — how to run the product safely after migration.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.continuity_confidence.models import PostRestoreSafeOperatingGuidance
from workflow_dataset.continuity_confidence.device_profile import build_target_device_profile
from workflow_dataset.continuity_confidence.device_classes import resolve_device_class
from workflow_dataset.continuity_confidence.post_restore_presets import get_recommended_preset_for
from workflow_dataset.continuity_confidence.confidence import build_continuity_confidence


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def post_restore_safe_operating_guidance(
    bundle_ref: str = "latest",
    repo_root: Path | str | None = None,
) -> PostRestoreSafeOperatingGuidance:
    """
    Build operator-facing guidance on how to run the product safely after migration.
    Uses target device profile, resolved device class, continuity confidence, and recommended preset.
    """
    root = _root(repo_root)
    now = utc_now_iso()

    target = build_target_device_profile(repo_root=root)
    device_class = resolve_device_class(target)
    score, _, _, posture = build_continuity_confidence(bundle_ref=bundle_ref, repo_root=root)
    preset = get_recommended_preset_for(
        device_class_id=device_class.class_id,
        confidence_class=score.classification,
    )

    do_list = list(preset.do_after_migration)
    avoid_list = list(preset.avoid_after_migration)
    if not do_list and posture:
        do_list.append(posture.next_review_action or "Run continuity-confidence report")
    if preset.require_review_before_production and "Do not enable operator mode" not in str(avoid_list):
        avoid_list.append("Do not enable operator mode until review is complete.")

    summary_parts = [
        f"Device class: {device_class.label}.",
        f"Recommended preset: {preset.label}.",
    ]
    if preset.production_cut_narrowed:
        summary_parts.append("Narrow production cut until review is complete.")
    if not preset.operator_mode_trusted:
        summary_parts.append("Operator mode should not be trusted until review.")
    summary = " ".join(summary_parts)

    return PostRestoreSafeOperatingGuidance(
        device_class_id=device_class.class_id,
        device_class_label=device_class.label,
        recommended_preset_id=preset.preset_id,
        recommended_preset_label=preset.label,
        do_after_migration=do_list,
        avoid_after_migration=avoid_list,
        summary=summary,
        next_review_action=preset.next_review_action or "workflow-dataset continuity-confidence report",
        generated_at_utc=now,
    )

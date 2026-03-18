"""
M49I–M49L: Continuity confidence — classify post-restore confidence, downgraded/promoted notes, recommended posture.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.continuity_confidence.models import (
    ContinuityConfidenceScore,
    ContinuityConfidenceClass,
    DowngradedCapabilityNote,
    PromotedCapabilityNote,
    RecommendedOperatingPosture,
    DeviceCapabilityClass,
)
from workflow_dataset.continuity_confidence.device_profile import build_target_device_profile, compare_source_target
from workflow_dataset.migration_restore.validation import validate_bundle_for_target
from workflow_dataset.migration_restore.bundle import get_bundle_manifest


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def build_continuity_confidence(
    bundle_ref: str = "latest",
    repo_root: Path | str | None = None,
) -> tuple[ContinuityConfidenceScore, list[DowngradedCapabilityNote], list[PromotedCapabilityNote], RecommendedOperatingPosture | None]:
    """
    Build continuity confidence from restore validation + target device profile.
    Returns (score, downgraded_notes, promoted_notes, recommended_posture).
    """
    root = _root(repo_root)
    now = utc_now_iso()
    report = validate_bundle_for_target(bundle_ref, target_repo_root=root)
    restore_score = report.restore_confidence.score if report.restore_confidence else 0.0
    restore_label = report.restore_confidence.label if report.restore_confidence else "unknown"
    restore_reasons = report.restore_confidence.reasons if report.restore_confidence else []

    target_profile = build_target_device_profile(repo_root=root)
    # Optional: source profile from bundle manifest (we don't have stored source device; treat as same/unknown)
    capability_class = DeviceCapabilityClass.UNKNOWN.value

    downgraded: list[DowngradedCapabilityNote] = []
    promoted: list[PromotedCapabilityNote] = []

    if not report.passed:
        classification = ContinuityConfidenceClass.BLOCKED.value
        label = "Restore blocked; fix blockers before relying on continuity."
        posture = None
    elif restore_score >= 0.9 and not report.warnings:
        classification = ContinuityConfidenceClass.HIGH_CONFIDENCE.value
        label = "High-confidence continuity; restored deployment matches target."
        posture = RecommendedOperatingPosture(
            posture_id="high_confidence",
            label="Full operation",
            description="Operator mode and production cut can be used as configured after review.",
            production_cut_narrowed=False,
            operator_mode_trusted=True,
            require_review_before_production=False,
            next_review_action="Optional: workflow-dataset continuity-confidence report",
            created_utc=now,
        )
    elif restore_score >= 0.7 and report.warnings:
        classification = ContinuityConfidenceClass.NARROWED_PRODUCTION_CUT.value
        label = "Restore succeeded but production cut should be narrowed."
        for w in report.warnings[:5]:
            downgraded.append(DowngradedCapabilityNote(
                note_id="downgrade_" + w[:20].replace(" ", "_"),
                subsystem_or_feature="restore",
                description=w,
                recommendation="Narrow production cut until warnings are resolved.",
                created_utc=now,
            ))
        posture = RecommendedOperatingPosture(
            posture_id="narrowed_production_cut",
            label="Narrow production cut",
            description="Restore ok; narrow production cut and review before full production use.",
            production_cut_narrowed=True,
            operator_mode_trusted=False,
            require_review_before_production=True,
            next_review_action="workflow-dataset continuity-confidence report",
            created_utc=now,
        )
    elif restore_score >= 0.5 and report.warnings:
        classification = ContinuityConfidenceClass.USABLE_DEGRADED.value
        label = "Usable with degraded capabilities; review warnings."
        for w in report.warnings[:5]:
            downgraded.append(DowngradedCapabilityNote(
                note_id="downgrade_" + w[:20].replace(" ", "_"),
                subsystem_or_feature="restore",
                description=w,
                recommendation="Review migration_restore validation warnings.",
                created_utc=now,
            ))
        posture = RecommendedOperatingPosture(
            posture_id="usable_degraded",
            label="Use with care",
            description="Some capabilities may be degraded; narrow production cut if needed.",
            production_cut_narrowed=True,
            operator_mode_trusted=False,
            require_review_before_production=True,
            next_review_action="workflow-dataset continuity-confidence report",
            created_utc=now,
        )
    elif restore_score >= 0.5:
        classification = ContinuityConfidenceClass.REVIEW_REQUIRED.value
        label = "Review required before production use."
        posture = RecommendedOperatingPosture(
            posture_id="review_required",
            label="Review before production",
            description="Run continuity-confidence report and fix any issues before production.",
            production_cut_narrowed=True,
            operator_mode_trusted=False,
            require_review_before_production=True,
            next_review_action="workflow-dataset continuity-confidence report",
            created_utc=now,
        )
    else:
        classification = ContinuityConfidenceClass.OPERATOR_MODE_NOT_TRUSTED.value
        label = "Restore succeeded but operator mode should not be trusted until reviewed."
        posture = RecommendedOperatingPosture(
            posture_id="operator_not_trusted",
            label="Do not trust operator mode yet",
            description="Narrow production cut and review before enabling operator mode.",
            production_cut_narrowed=True,
            operator_mode_trusted=False,
            require_review_before_production=True,
            next_review_action="workflow-dataset continuity-confidence explain",
            created_utc=now,
        )

    if capability_class == DeviceCapabilityClass.STRONGER.value:
        promoted.append(PromotedCapabilityNote(
            note_id="promoted_target",
            subsystem_or_feature="device",
            description="Target device has stronger or additional capabilities than source.",
            created_utc=now,
        ))

    reasons = list(restore_reasons)
    if not reasons and classification != ContinuityConfidenceClass.HIGH_CONFIDENCE.value:
        reasons.append(label)

    score = ContinuityConfidenceScore(
        score=restore_score,
        classification=classification,
        label=label,
        reasons=reasons,
        generated_at_utc=now,
    )
    return score, downgraded, promoted, posture

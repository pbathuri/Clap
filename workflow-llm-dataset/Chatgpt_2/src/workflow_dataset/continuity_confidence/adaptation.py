"""
M49I–M49L: Post-restore runtime adaptation — model/route adjustment, operator-mode safety, recommendations.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.continuity_confidence.models import (
    PostRestoreRuntimeProfile,
    ModelRouteAdjustment,
    OperatorModeSafetyAdjustment,
    ContinuityConfidenceClass,
)
from workflow_dataset.continuity_confidence.device_profile import build_target_device_profile
from workflow_dataset.continuity_confidence.confidence import build_continuity_confidence


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def build_post_restore_runtime_profile(
    bundle_ref: str = "latest",
    repo_root: Path | str | None = None,
) -> tuple[PostRestoreRuntimeProfile, list[ModelRouteAdjustment], list[OperatorModeSafetyAdjustment]]:
    """
    Build post-restore runtime profile and adjustment recommendations from confidence and device profile.
    Returns (post_restore_profile, model_route_adjustments, operator_mode_adjustments).
    """
    root = _root(repo_root)
    now = utc_now_iso()
    target = build_target_device_profile(repo_root=root)
    score, downgraded, _, posture = build_continuity_confidence(bundle_ref=bundle_ref, repo_root=root)

    profile_id = f"post_restore_{target.profile_id}"
    recommended_policy = "balanced"
    production_cut_narrowed = False
    operator_mode_ready = False
    operator_mode_scope_note = ""

    if posture:
        production_cut_narrowed = posture.production_cut_narrowed
        operator_mode_ready = posture.operator_mode_trusted
        operator_mode_scope_note = posture.description if not posture.operator_mode_trusted else ""

    if score.classification in (ContinuityConfidenceClass.USABLE_DEGRADED.value, ContinuityConfidenceClass.REVIEW_REQUIRED.value):
        recommended_policy = "conservative"
    if score.classification == ContinuityConfidenceClass.OPERATOR_MODE_NOT_TRUSTED.value:
        recommended_policy = "conservative"
        production_cut_narrowed = True

    post_profile = PostRestoreRuntimeProfile(
        profile_id=profile_id,
        target_device_profile_id=target.profile_id,
        recommended_routing_policy_id=recommended_policy,
        recommended_vertical_id="default",
        production_cut_narrowed=production_cut_narrowed,
        production_cut_scope_note="Narrow production cut until post-restore review." if production_cut_narrowed else "",
        allow_degraded_fallback=target.has_llm_backend,
        operator_mode_ready=operator_mode_ready,
        operator_mode_scope_note=operator_mode_scope_note or "Review before enabling operator mode.",
        created_utc=now,
    )

    route_adjustments: list[ModelRouteAdjustment] = []
    if not target.has_llm_backend and score.classification != ContinuityConfidenceClass.HIGH_CONFIDENCE.value:
        route_adjustments.append(ModelRouteAdjustment(
            adjustment_id="route_llm",
            task_family_or_vertical="default",
            current_route="primary",
            recommended_route="suggestion_only_or_install_backend",
            reason="Target has no LLM backend available; use suggestion-only or install backend.",
            created_utc=now,
        ))

    op_adjustments: list[OperatorModeSafetyAdjustment] = []
    if not operator_mode_ready:
        op_adjustments.append(OperatorModeSafetyAdjustment(
            adjustment_id="op_suspend_or_review",
            scope_or_domain="operator_routine",
            recommended_action="allow_after_review",
            reason="Post-restore: operator mode not trusted until review.",
            created_utc=now,
        ))

    return post_profile, route_adjustments, op_adjustments


def get_downgraded_runtime_explanation(
    bundle_ref: str = "latest",
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Return operator-facing explanation when runtime is downgraded after restore.
    """
    root = _root(repo_root)
    score, downgraded, promoted, posture = build_continuity_confidence(bundle_ref=bundle_ref, repo_root=root)
    post_profile, route_adj, op_adj = build_post_restore_runtime_profile(bundle_ref=bundle_ref, repo_root=root)

    return {
        "continuity_classification": score.classification,
        "continuity_label": score.label,
        "downgraded_capabilities": [n.to_dict() for n in downgraded],
        "promoted_capabilities": [n.to_dict() for n in promoted],
        "production_cut_narrowed": post_profile.production_cut_narrowed,
        "operator_mode_ready": post_profile.operator_mode_ready,
        "model_route_adjustments": [a.to_dict() for a in route_adj],
        "operator_mode_adjustments": [a.to_dict() for a in op_adj],
        "recommended_posture": posture.to_dict() if posture else None,
        "next_review_action": posture.next_review_action if posture else "workflow-dataset continuity-confidence report",
    }

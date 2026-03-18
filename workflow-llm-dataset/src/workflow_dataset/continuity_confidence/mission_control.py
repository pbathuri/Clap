"""
M49I–M49L: Mission control slice — post-restore confidence, downgraded warnings, operator-mode readiness.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.continuity_confidence.confidence import build_continuity_confidence
from workflow_dataset.continuity_confidence.adaptation import build_post_restore_runtime_profile


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def continuity_confidence_slice(repo_root: Path | str | None = None) -> dict[str, Any]:
    """Build mission-control slice: current post-restore confidence, downgraded warnings, restored but narrowed, next review, operator-mode readiness."""
    try:
        root = _root(repo_root)
        score, downgraded, _, posture = build_continuity_confidence(bundle_ref="latest", repo_root=root)
        post_profile, _, _ = build_post_restore_runtime_profile(bundle_ref="latest", repo_root=root)

        downgraded_warnings = [n.description for n in downgraded[:5]]
        next_review = posture.next_review_action if posture else "workflow-dataset continuity-confidence report"

        return {
            "current_post_restore_confidence": score.classification,
            "current_post_restore_confidence_label": score.label,
            "current_post_restore_confidence_score": score.score,
            "downgraded_runtime_profile_warnings": downgraded_warnings,
            "restored_but_narrowed_features": post_profile.production_cut_scope_note or (["production_cut_narrowed"] if post_profile.production_cut_narrowed else []),
            "next_recommended_post_restore_review": next_review,
            "operator_mode_readiness_after_restore": post_profile.operator_mode_ready,
            "operator_mode_scope_note": post_profile.operator_mode_scope_note,
        }
    except Exception as e:
        return {"error": str(e)}

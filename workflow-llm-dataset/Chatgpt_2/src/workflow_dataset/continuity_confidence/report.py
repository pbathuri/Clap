"""
M49I–M49L: Full continuity confidence report for CLI and mission control.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.continuity_confidence.confidence import build_continuity_confidence
from workflow_dataset.continuity_confidence.adaptation import (
    build_post_restore_runtime_profile,
    get_downgraded_runtime_explanation,
)
from workflow_dataset.continuity_confidence.device_profile import build_target_device_profile


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def continuity_confidence_report(
    bundle_ref: str = "latest",
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Build full continuity confidence report: device profile, confidence score, downgraded/promoted notes,
    post-restore profile, adjustments, recommended posture.
    """
    root = _root(repo_root)
    target = build_target_device_profile(repo_root=root)
    score, downgraded, promoted, posture = build_continuity_confidence(bundle_ref=bundle_ref, repo_root=root)
    post_profile, route_adj, op_adj = build_post_restore_runtime_profile(bundle_ref=bundle_ref, repo_root=root)

    return {
        "bundle_ref": bundle_ref,
        "target_device_profile": target.to_dict(),
        "continuity_confidence": score.to_dict(),
        "downgraded_capabilities": [n.to_dict() for n in downgraded],
        "promoted_capabilities": [n.to_dict() for n in promoted],
        "post_restore_runtime_profile": post_profile.to_dict(),
        "model_route_adjustments": [a.to_dict() for a in route_adj],
        "operator_mode_adjustments": [a.to_dict() for a in op_adj],
        "recommended_operating_posture": posture.to_dict() if posture else None,
        "downgraded_explanation": get_downgraded_runtime_explanation(bundle_ref=bundle_ref, repo_root=root),
    }

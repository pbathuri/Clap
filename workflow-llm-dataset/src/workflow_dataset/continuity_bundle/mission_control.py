"""
M49D: Mission control slice — latest bundle, transfer-sensitive, excluded local-only, next portability review.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.continuity_bundle.build import inspect_bundle
from workflow_dataset.continuity_bundle.portability import get_portability_boundaries
from workflow_dataset.continuity_bundle.reports import get_portability_report
from workflow_dataset.continuity_bundle.models import TransferClass


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def continuity_bundle_slice(repo_root: Path | str | None = None) -> dict[str, Any]:
    """
    Additive mission-control slice for continuity bundle.
    Keys: latest_bundle_ref, latest_bundle_id, transfer_sensitive_components, excluded_local_only,
    next_portability_review.
    """
    root = _root(repo_root)
    bundle = inspect_bundle("latest", root)
    latest_id = bundle.bundle_id if bundle else None
    boundaries = get_portability_boundaries(root)
    transfer_sensitive = boundaries.get("transfer_with_review", []) + boundaries.get("experimental_transfer", [])
    excluded = boundaries.get("local_only", [])
    # M49D.1: operator-facing report summary (default policy: transfer_with_review)
    portability_report = get_portability_report(root, sensitivity_policy_id="transfer_with_review")
    return {
        "latest_bundle_ref": "latest" if latest_id else None,
        "latest_bundle_id": latest_id,
        "bundle_profile_id": (bundle.profile_id if bundle and getattr(bundle, "profile_id", "") else None) or None,
        "transfer_sensitive_components": transfer_sensitive[:10],
        "transfer_sensitive_count": len(transfer_sensitive),
        "excluded_local_only": excluded,
        "excluded_local_only_count": len(excluded),
        "safe_to_transfer_count": len(boundaries.get("safe_to_transfer", [])),
        "portability_report_summary": portability_report.get("summary", ""),
        "portable_count": portability_report.get("portable_count", 0),
        "review_required_count": portability_report.get("review_required_count", 0),
        "excluded_count": portability_report.get("excluded_count", 0),
        "rebuild_only_count": portability_report.get("rebuild_only_count", 0),
        "next_portability_review": "workflow-dataset continuity-bundle report",
    }

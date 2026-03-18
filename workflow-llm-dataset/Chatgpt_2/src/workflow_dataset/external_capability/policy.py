"""
M24A: Policy and rejection layer — unsupported license, resource cost, not useful for profile,
unsafe trust posture, incompatible machine, remote-only when local-first required.
"""

from __future__ import annotations

from typing import Any

from workflow_dataset.external_capability.schema import ExternalCapabilitySource

# Rejection reason codes (for reports and mission control)
REJECTION_UNSUPPORTED_LICENSE = "unsupported_license"
REJECTION_RESOURCE_TOO_HIGH = "resource_too_high"
REJECTION_NOT_USEFUL_FOR_PROFILE = "not_useful_for_profile"
REJECTION_UNSAFE_TRUST_POSTURE = "unsafe_trust_posture"
REJECTION_INCOMPATIBLE_MACHINE = "incompatible_machine"
REJECTION_REMOTE_ONLY_LOCAL_FIRST = "remote_only_local_first"
REJECTION_MISSING_APPROVALS = "missing_approvals"


def apply_rejection_policy(
    source: ExternalCapabilitySource,
    machine_profile: dict[str, Any],
    trust_posture: dict[str, Any],
    domain_pack_id: str | None = None,
    task_class: str | None = None,
) -> tuple[bool, str]:
    """
    Decide if source is allowed for activation given machine, trust, and optional domain/task.
    Returns (allowed, reason). reason is empty when allowed; otherwise rejection code or message.
    """
    # Local-first: reject remote-only when product requires local
    if not source.local and source.optional_remote is False:
        return False, REJECTION_REMOTE_ONLY_LOCAL_FIRST

    tier = (machine_profile or {}).get("tier") or (machine_profile or {}).get("edge_profile", {}).get("tier")
    if not tier:
        tier = "local_standard"
    supported_tiers = source.supported_tiers or ["dev_full", "local_standard"]
    if tier not in supported_tiers:
        return False, REJECTION_INCOMPATIBLE_MACHINE

    # License: reject known bad (placeholder; expand from OPEN_SOURCE_REJECTION_CRITERIA)
    bad_licenses = ("proprietary", "unlicensed")
    if (source.license_policy or "").lower() in bad_licenses:
        return False, REJECTION_UNSUPPORTED_LICENSE

    # Resource: if machine is constrained_edge or minimal_eval and source is high, reject
    if tier in ("constrained_edge", "minimal_eval") and (source.estimated_resource or "").lower() == "high":
        return False, REJECTION_RESOURCE_TOO_HIGH

    # Trust: if safe_to_expand is False and source requires approval, can still allow but caller may block
    safe = trust_posture.get("safe_to_expand", True)
    if not safe and source.approval_notes and not trust_posture.get("approval_registry_exists"):
        return False, REJECTION_UNSAFE_TRUST_POSTURE

    # Domain/task usefulness: if domain_pack or task_class requested and source doesn't support, not useful
    if domain_pack_id and source.supported_domain_pack_ids and domain_pack_id not in source.supported_domain_pack_ids:
        return False, REJECTION_NOT_USEFUL_FOR_PROFILE
    if task_class and source.supported_task_classes and task_class not in source.supported_task_classes:
        return False, REJECTION_NOT_USEFUL_FOR_PROFILE

    return True, ""

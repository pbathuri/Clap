"""
M49D.1: Sensitivity policies for transfer — govern what is portable, review-required, or excluded.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from workflow_dataset.continuity_bundle.models import TransferClass


@dataclass
class SensitivityPolicy:
    """Policy governing transfer sensitivity: what to allow, require review for, or exclude."""
    policy_id: str = ""
    label: str = ""
    description: str = ""
    allow_sensitive: bool = True   # include transfer_with_review sensitive components
    require_review_for_sensitive: bool = True
    allow_experimental: bool = False
    exclude_local_only: bool = True
    treat_rebuild_as_excluded: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "label": self.label,
            "description": self.description,
            "allow_sensitive": self.allow_sensitive,
            "require_review_for_sensitive": self.require_review_for_sensitive,
            "allow_experimental": self.allow_experimental,
            "exclude_local_only": self.exclude_local_only,
            "treat_rebuild_as_excluded": self.treat_rebuild_as_excluded,
        }


# Built-in sensitivity policies
POLICY_TRANSFER_WITH_REVIEW = "transfer_with_review"
POLICY_EXCLUDE_SENSITIVE = "exclude_sensitive"
POLICY_STRICT_SAFE_ONLY = "strict_safe_only"

SENSITIVITY_POLICIES: list[SensitivityPolicy] = [
    SensitivityPolicy(
        policy_id=POLICY_TRANSFER_WITH_REVIEW,
        label="Transfer with review",
        description="Sensitive and experimental components allowed; must be reviewed before restore.",
        allow_sensitive=True,
        require_review_for_sensitive=True,
        allow_experimental=True,
        exclude_local_only=True,
        treat_rebuild_as_excluded=True,
    ),
    SensitivityPolicy(
        policy_id=POLICY_EXCLUDE_SENSITIVE,
        label="Exclude sensitive",
        description="Only safe-to-transfer components; sensitive and experimental excluded.",
        allow_sensitive=False,
        require_review_for_sensitive=False,
        allow_experimental=False,
        exclude_local_only=True,
        treat_rebuild_as_excluded=True,
    ),
    SensitivityPolicy(
        policy_id=POLICY_STRICT_SAFE_ONLY,
        label="Strict safe only",
        description="Portable set is strictly safe_to_transfer; everything else excluded or rebuild-only.",
        allow_sensitive=False,
        require_review_for_sensitive=False,
        allow_experimental=False,
        exclude_local_only=True,
        treat_rebuild_as_excluded=True,
    ),
]


def get_sensitivity_policy(policy_id: str) -> SensitivityPolicy | None:
    """Return sensitivity policy by id."""
    for p in SENSITIVITY_POLICIES:
        if p.policy_id == policy_id:
            return p
    return None


def list_sensitivity_policies() -> list[SensitivityPolicy]:
    """Return all built-in sensitivity policies."""
    return list(SENSITIVITY_POLICIES)


def apply_policy_to_boundaries(
    boundaries: dict[str, Any],
    policy: SensitivityPolicy,
) -> dict[str, Any]:
    """
    Apply sensitivity policy to portability boundaries.
    Returns dict with: portable, review_required, excluded, rebuild_only, summary.
    """
    safe = list(boundaries.get("safe_to_transfer", []))
    review = list(boundaries.get("transfer_with_review", []))
    local_only = list(boundaries.get("local_only", []))
    rebuild = list(boundaries.get("rebuild_on_restore", []))
    experimental = list(boundaries.get("experimental_transfer", []))

    portable: list[str] = list(safe)
    review_required: list[str] = []
    excluded: list[str] = list(local_only)
    rebuild_only: list[str] = list(rebuild) if policy.treat_rebuild_as_excluded else []

    if policy.allow_sensitive:
        review_required.extend(review)
    else:
        excluded.extend(review)

    if policy.allow_experimental:
        review_required.extend(experimental)
    else:
        excluded.extend(experimental)

    if not policy.exclude_local_only:
        portable.extend(local_only)
        excluded = [x for x in excluded if x not in local_only]

    return {
        "portable": portable,
        "review_required": review_required,
        "excluded": excluded,
        "rebuild_only": rebuild_only,
        "portable_count": len(portable),
        "review_required_count": len(review_required),
        "excluded_count": len(excluded),
        "rebuild_only_count": len(rebuild_only),
        "summary": f"portable={len(portable)} review_required={len(review_required)} excluded={len(excluded)} rebuild_only={len(rebuild_only)}",
        "policy_id": policy.policy_id,
        "policy_label": policy.label,
    }

"""
M49D.1: Bundle profiles — personal-core, production-cut, maintenance-safe.
Profiles define default include/exclude/transfer-class sets for bundle creation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from workflow_dataset.continuity_bundle.models import TransferClass


@dataclass
class BundleProfile:
    """Named profile for continuity bundle creation: default component and transfer-class sets."""
    profile_id: str = ""
    label: str = ""
    description: str = ""
    include_component_ids: list[str] | None = None  # None = all portable; [] = none
    exclude_component_ids: list[str] = field(default_factory=list)
    include_transfer_classes: list[str] | None = None  # None = all except local_only

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "label": self.label,
            "description": self.description,
            "include_component_ids": self.include_component_ids,
            "exclude_component_ids": list(self.exclude_component_ids),
            "include_transfer_classes": self.include_transfer_classes,
        }


# Built-in bundle profiles
PROFILE_PERSONAL_CORE = "personal_core"
PROFILE_PRODUCTION_CUT = "production_cut"
PROFILE_MAINTENANCE_SAFE = "maintenance_safe"

BUNDLE_PROFILES: list[BundleProfile] = [
    BundleProfile(
        profile_id=PROFILE_PERSONAL_CORE,
        label="Personal core",
        description="Workday, continuity, project/session, operator mode, governance preset. Excludes production cut and trust contracts unless explicitly added.",
        include_component_ids=None,
        exclude_component_ids=["production_cut", "trust_contracts", "memory_curation_index", "background_queue"],
        include_transfer_classes=None,
    ),
    BundleProfile(
        profile_id=PROFILE_PRODUCTION_CUT,
        label="Production cut",
        description="Full portable set including production cut and trust contracts; all transfer-with-review and safe components. For machine swap with locked cut.",
        include_component_ids=None,
        exclude_component_ids=["background_queue"],
        include_transfer_classes=[TransferClass.SAFE_TO_TRANSFER.value, TransferClass.TRANSFER_WITH_REVIEW.value],
    ),
    BundleProfile(
        profile_id=PROFILE_MAINTENANCE_SAFE,
        label="Maintenance safe",
        description="Safe-to-transfer only; no sensitive or review-required components. For low-risk backup or audit.",
        include_component_ids=None,
        exclude_component_ids=[],
        include_transfer_classes=[TransferClass.SAFE_TO_TRANSFER.value],
    ),
]


def get_profile(profile_id: str) -> BundleProfile | None:
    """Return bundle profile by id."""
    for p in BUNDLE_PROFILES:
        if p.profile_id == profile_id:
            return p
    return None


def list_profiles() -> list[BundleProfile]:
    """Return all built-in bundle profiles."""
    return list(BUNDLE_PROFILES)


def resolve_profile_components(
    profile_id: str,
    all_component_ids: list[str],
) -> tuple[set[str] | None, set[str], set[str] | None]:
    """
    Resolve profile into (include_set or None, exclude_set, include_transfer_classes or None).
    - include_set None means "no filter by id"; otherwise only these ids are included.
    - exclude_set is always applied.
    - include_transfer_classes None means "all except local_only"; otherwise only these transfer classes.
    """
    profile = get_profile(profile_id)
    if profile is None:
        return None, set(), None
    exclude_set = set(profile.exclude_component_ids or [])
    include_set = None
    if profile.include_component_ids is not None:
        include_set = set(profile.include_component_ids)
    class_set = None
    if profile.include_transfer_classes is not None:
        class_set = set(profile.include_transfer_classes)
    return include_set, exclude_set, class_set

"""
M49A: Portable state model — portable/non-portable state class, bundle component, continuity bundle, provenance.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TransferClass(str, Enum):
    """Portability boundary for a component."""
    SAFE_TO_TRANSFER = "safe_to_transfer"
    TRANSFER_WITH_REVIEW = "transfer_with_review"
    LOCAL_ONLY = "local_only"
    REBUILD_ON_RESTORE = "rebuild_on_restore"
    EXPERIMENTAL_TRANSFER = "experimental_transfer"


@dataclass
class PortableStateClass:
    """State class that is eligible for portable continuity (by component id)."""
    class_id: str = ""
    label: str = ""
    component_ids: list[str] = field(default_factory=list)
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "class_id": self.class_id,
            "label": self.label,
            "component_ids": list(self.component_ids),
            "description": self.description,
        }


@dataclass
class NonPortableStateClass:
    """State class that must not be transferred (local-machine or rebuild)."""
    class_id: str = ""
    label: str = ""
    component_ids: list[str] = field(default_factory=list)
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "class_id": self.class_id,
            "label": self.label,
            "component_ids": list(self.component_ids),
            "reason": self.reason,
        }


@dataclass
class BundleComponent:
    """One component in a continuity bundle: id, path, transfer class, flags, provenance."""
    component_id: str = ""
    path: str = ""
    path_pattern: str = ""  # e.g. data/local/workday/** for dir
    transfer_class: str = TransferClass.SAFE_TO_TRANSFER.value
    sensitive: bool = False
    review_required: bool = False
    optional: bool = False
    label: str = ""
    description: str = ""
    provenance: "BundleProvenance | None" = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "component_id": self.component_id,
            "path": self.path,
            "path_pattern": self.path_pattern,
            "transfer_class": self.transfer_class,
            "sensitive": self.sensitive,
            "review_required": self.review_required,
            "optional": self.optional,
            "label": self.label,
            "description": self.description,
            "provenance": self.provenance.to_dict() if self.provenance else None,
        }


@dataclass
class BundleProvenance:
    """Provenance and version metadata for a bundle or component."""
    product_version: str = ""
    created_at_utc: str = ""
    source_repo_root: str = ""
    bundle_id: str = ""
    component_version_hint: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "product_version": self.product_version,
            "created_at_utc": self.created_at_utc,
            "source_repo_root": self.source_repo_root,
            "bundle_id": self.bundle_id,
            "component_version_hint": self.component_version_hint,
        }


@dataclass
class ContinuityBundle:
    """Continuity bundle: manifest ref + list of components with transfer class and provenance."""
    bundle_id: str = ""
    created_at_utc: str = ""
    product_version: str = ""
    source_repo_root: str = ""
    components: list[BundleComponent] = field(default_factory=list)
    manifest_ref: str = ""  # migration_restore manifest or local path
    excluded_component_ids: list[str] = field(default_factory=list)
    profile_id: str = ""  # M49D.1: optional bundle profile used at creation

    def to_dict(self) -> dict[str, Any]:
        return {
            "bundle_id": self.bundle_id,
            "created_at_utc": self.created_at_utc,
            "product_version": self.product_version,
            "source_repo_root": self.source_repo_root,
            "components": [c.to_dict() for c in self.components],
            "manifest_ref": self.manifest_ref,
            "excluded_component_ids": list(self.excluded_component_ids),
            "profile_id": self.profile_id or None,
        }

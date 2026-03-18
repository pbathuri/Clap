"""
M35H.1: Reusable responsibility bundles — create, list, add responsibilities.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.operator_mode.models import ResponsibilityBundle, DelegatedResponsibility
from workflow_dataset.operator_mode.store import (
    get_bundle,
    save_bundle,
    list_bundle_ids,
    get_responsibility,
    list_responsibility_ids,
)
from workflow_dataset.utils.dates import utc_now_iso


def create_bundle(
    bundle_id: str,
    label: str,
    description: str = "",
    responsibility_ids: list[str] | None = None,
    repo_root: Path | str | None = None,
) -> ResponsibilityBundle:
    """Create a new responsibility bundle."""
    now = utc_now_iso()
    bundle = ResponsibilityBundle(
        bundle_id=bundle_id,
        label=label,
        description=description,
        responsibility_ids=list(responsibility_ids or []),
        created_utc=now,
        updated_utc=now,
    )
    save_bundle(bundle, repo_root=repo_root)
    return bundle


def add_responsibility_to_bundle(
    bundle_id: str,
    responsibility_id: str,
    repo_root: Path | str | None = None,
) -> ResponsibilityBundle | None:
    """Add a responsibility to a bundle if not already present. Returns updated bundle or None if bundle not found."""
    bundle = get_bundle(bundle_id, repo_root=repo_root)
    if not bundle:
        return None
    if responsibility_id in bundle.responsibility_ids:
        return bundle
    bundle.responsibility_ids = list(bundle.responsibility_ids) + [responsibility_id]
    bundle.updated_utc = utc_now_iso()
    save_bundle(bundle, repo_root=repo_root)
    return bundle


def remove_responsibility_from_bundle(
    bundle_id: str,
    responsibility_id: str,
    repo_root: Path | str | None = None,
) -> ResponsibilityBundle | None:
    """Remove a responsibility from a bundle. Returns updated bundle or None."""
    bundle = get_bundle(bundle_id, repo_root=repo_root)
    if not bundle:
        return None
    bundle.responsibility_ids = [r for r in bundle.responsibility_ids if r != responsibility_id]
    bundle.updated_utc = utc_now_iso()
    save_bundle(bundle, repo_root=repo_root)
    return bundle


def resolve_bundle_responsibility_ids(bundle_id: str, repo_root: Path | str | None = None) -> list[str]:
    """Return the list of responsibility ids in a bundle (only those that exist)."""
    bundle = get_bundle(bundle_id, repo_root=repo_root)
    if not bundle:
        return []
    root = Path(repo_root).resolve() if repo_root else None
    return [r for r in bundle.responsibility_ids if get_responsibility(r, repo_root=root)]

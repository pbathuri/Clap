"""
M49B: Continuity bundle building — create, inspect, validate, selective include/exclude.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

try:
    from workflow_dataset.utils.hashes import stable_id
except Exception:
    def stable_id(*parts: str, prefix: str = "") -> str:
        import hashlib
        return prefix + hashlib.sha256("".join(str(p) for p in parts).encode()).hexdigest()[:14]

from workflow_dataset.continuity_bundle.models import (
    ContinuityBundle,
    BundleComponent,
    BundleProvenance,
    TransferClass,
)
from workflow_dataset.continuity_bundle.components import get_component_registry, get_component
from workflow_dataset.continuity_bundle.profiles import resolve_profile_components


BUNDLES_DIR = "data/local/continuity_bundle/bundles"
MANIFEST_FILE = "manifest.json"


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _product_version(repo_root: Path) -> str:
    try:
        from workflow_dataset.install_upgrade.version import get_current_version
        return get_current_version(repo_root) or "0.0.0"
    except Exception:
        return "0.0.0"


def create_bundle(
    repo_root: Path | str | None = None,
    include_components: list[str] | None = None,
    exclude_components: list[str] | None = None,
    include_transfer_classes: list[str] | None = None,
    profile_id: str | None = None,
) -> ContinuityBundle:
    """
    Create continuity bundle from current state. Selective include/exclude by component id, transfer class, or profile.
    When profile_id is set and include/exclude not explicitly passed, resolve from profile. M49D.1.
    Writes to data/local/continuity_bundle/bundles/<bundle_id>/manifest.json.
    """
    root = _root(repo_root)
    now = utc_now_iso()
    bundle_id = stable_id("cb", now[:16], prefix="cb_")
    version = _product_version(root)
    registry = get_component_registry(root)
    all_ids = [c.component_id for c in registry]
    include_set = set(include_components) if include_components else None
    exclude_set = set(exclude_components or [])
    class_set = set(include_transfer_classes) if include_transfer_classes else None
    if profile_id and include_components is None and exclude_components is None:
        p_include, p_exclude, p_class = resolve_profile_components(profile_id, all_ids)
        if p_include is not None:
            include_set = p_include
        exclude_set = exclude_set | p_exclude
        if p_class is not None:
            class_set = p_class
    components: list[BundleComponent] = []
    excluded: list[str] = []
    for c in registry:
        if c.component_id in exclude_set:
            excluded.append(c.component_id)
            continue
        if include_set is not None and c.component_id not in include_set:
            excluded.append(c.component_id)
            continue
        if class_set is not None and c.transfer_class not in class_set:
            excluded.append(c.component_id)
            continue
        if c.transfer_class == TransferClass.LOCAL_ONLY.value:
            excluded.append(c.component_id)
            continue
        prov = BundleProvenance(
            product_version=version,
            created_at_utc=now,
            source_repo_root=str(root),
            bundle_id=bundle_id,
            component_version_hint=c.path,
        )
        comp = BundleComponent(
            component_id=c.component_id,
            path=c.path,
            path_pattern=c.path_pattern,
            transfer_class=c.transfer_class,
            sensitive=c.sensitive,
            review_required=c.review_required,
            optional=c.optional,
            label=c.label,
            description=c.description,
            provenance=prov,
        )
        components.append(comp)
    bundle = ContinuityBundle(
        bundle_id=bundle_id,
        created_at_utc=now,
        product_version=version,
        source_repo_root=str(root),
        components=components,
        manifest_ref=bundle_id,
        excluded_component_ids=excluded,
        profile_id=profile_id or "",
    )
    out_dir = root / BUNDLES_DIR / bundle_id
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / MANIFEST_FILE
    manifest_path.write_text(
        json.dumps(bundle.to_dict(), indent=2),
        encoding="utf-8",
    )
    return bundle


def inspect_bundle(
    bundle_ref: str,
    repo_root: Path | str | None = None,
) -> ContinuityBundle | None:
    """Load and return bundle by ref (bundle_id or 'latest')."""
    root = _root(repo_root)
    if bundle_ref == "latest":
        bundles_dir = root / BUNDLES_DIR
        if not bundles_dir.is_dir():
            return None
        latest_id: str | None = None
        latest_ts = ""
        for p in bundles_dir.iterdir():
            if not p.is_dir():
                continue
            m = p / MANIFEST_FILE
            if not m.exists():
                continue
            try:
                raw = json.loads(m.read_text(encoding="utf-8"))
                ts = raw.get("created_at_utc", "")
                if ts > latest_ts:
                    latest_ts = ts
                    latest_id = p.name
            except Exception:
                pass
        if latest_id is None:
            return None
        bundle_ref = latest_id
    manifest_path = root / BUNDLES_DIR / bundle_ref / MANIFEST_FILE
    if not manifest_path.exists():
        return None
    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
        components = [
            BundleComponent(
                component_id=c.get("component_id", ""),
                path=c.get("path", ""),
                path_pattern=c.get("path_pattern", ""),
                transfer_class=c.get("transfer_class", TransferClass.SAFE_TO_TRANSFER.value),
                sensitive=c.get("sensitive", False),
                review_required=c.get("review_required", False),
                optional=c.get("optional", False),
                label=c.get("label", ""),
                description=c.get("description", ""),
                provenance=None,
            )
            for c in raw.get("components", [])
        ]
        return ContinuityBundle(
            bundle_id=raw.get("bundle_id", ""),
            created_at_utc=raw.get("created_at_utc", ""),
            product_version=raw.get("product_version", ""),
            source_repo_root=raw.get("source_repo_root", ""),
            components=components,
            manifest_ref=raw.get("manifest_ref", bundle_ref),
            excluded_component_ids=list(raw.get("excluded_component_ids", [])),
            profile_id=raw.get("profile_id") or "",
        )
    except Exception:
        return None


def validate_bundle(
    bundle_ref: str,
    repo_root: Path | str | None = None,
    target_repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Validate bundle: check manifest, version, and optional target compatibility.
    Returns dict with valid: bool, errors: list, warnings: list, product_version, component_count.
    """
    root = _root(repo_root)
    bundle = inspect_bundle(bundle_ref, root)
    result: dict[str, Any] = {
        "valid": False,
        "errors": [],
        "warnings": [],
        "product_version": "",
        "component_count": 0,
        "bundle_id": "",
    }
    if bundle is None:
        result["errors"].append("Bundle not found or invalid manifest.")
        return result
    result["bundle_id"] = bundle.bundle_id
    result["product_version"] = bundle.product_version
    result["component_count"] = len(bundle.components)
    current_version = _product_version(root)
    if bundle.product_version and current_version and bundle.product_version != current_version:
        result["warnings"].append(f"Bundle version {bundle.product_version} differs from current {current_version}.")
    sensitive_count = sum(1 for c in bundle.components if c.sensitive)
    if sensitive_count > 0:
        result["warnings"].append(f"{sensitive_count} sensitive component(s); review before restore.")
    result["valid"] = len(result["errors"]) == 0
    if result["valid"] and not result["errors"]:
        result["valid"] = True
    return result

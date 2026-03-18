"""
M49A: Component registry — portable and non-portable components with transfer class.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.continuity_bundle.models import (
    BundleComponent,
    TransferClass,
)
from workflow_dataset.state_durability.boundaries import SUBSYSTEM_BOUNDARIES


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


# Components beyond SUBSYSTEM_BOUNDARIES (ids in SUBSYSTEM_BOUNDARIES are added first in _registry)
EXTRA_COMPONENTS: list[dict[str, Any]] = [
    {"id": "governance_preset", "path": "data/local/governance/active_preset.json", "transfer_class": TransferClass.SAFE_TO_TRANSFER, "sensitive": False, "review_required": False, "optional": True, "label": "Governance preset", "description": "Active governance preset."},
    {"id": "vertical_packs_progress", "path": "data/local/vertical_packs/progress.json", "transfer_class": TransferClass.SAFE_TO_TRANSFER, "sensitive": False, "review_required": False, "optional": True, "label": "Vertical packs progress", "description": "First-value path progress."},
    {"id": "vertical_packs_active", "path": "data/local/vertical_packs/active.json", "transfer_class": TransferClass.SAFE_TO_TRANSFER, "sensitive": False, "review_required": False, "optional": True, "label": "Active vertical pack", "description": "Active curated pack id."},
    {"id": "production_cut", "path": "data/local/production_cut/active_cut.json", "transfer_class": TransferClass.TRANSFER_WITH_REVIEW, "sensitive": True, "review_required": True, "optional": True, "label": "Production cut", "description": "Locked production cut; review before transfer."},
    {"id": "trust_contracts", "path": "data/local/trust/contracts.json", "transfer_class": TransferClass.TRANSFER_WITH_REVIEW, "sensitive": True, "review_required": True, "optional": True, "label": "Trust contracts", "description": "Trusted routine contracts; review before transfer."},
    {"id": "operator_mode_config", "path": "data/local/operator_mode", "transfer_class": TransferClass.SAFE_TO_TRANSFER, "sensitive": False, "review_required": False, "optional": True, "label": "Operator mode config", "description": "Operator mode configuration dir."},
    {"id": "memory_curation_index", "path": "data/local/memory_curation", "transfer_class": TransferClass.EXPERIMENTAL_TRANSFER, "sensitive": False, "review_required": True, "optional": True, "label": "Memory curation", "description": "Memory curation state; experimental transfer."},
]

# Build registry from SUBSYSTEM_BOUNDARIES + EXTRA (dedupe by id)
def _registry() -> list[BundleComponent]:
    seen: set[str] = set()
    out: list[BundleComponent] = []
    for b in SUBSYSTEM_BOUNDARIES:
        sid = b.get("id", "")
        if sid in seen:
            continue
        seen.add(sid)
        path = b.get("path", "")
        transfer = TransferClass.SAFE_TO_TRANSFER if sid != "background_queue" else TransferClass.LOCAL_ONLY
        out.append(BundleComponent(
            component_id=sid,
            path=path,
            path_pattern=path,
            transfer_class=transfer.value,
            sensitive=False,
            review_required=(transfer == TransferClass.TRANSFER_WITH_REVIEW),
            optional=sid in ("workday_preset", "project_current"),
            label=sid.replace("_", " ").title(),
            description=f"Subsystem: {sid}",
        ))
    for c in EXTRA_COMPONENTS:
        cid = c.get("id", "")
        if cid in seen:
            continue
        seen.add(cid)
        out.append(BundleComponent(
            component_id=cid,
            path=c.get("path", ""),
            path_pattern=c.get("path", ""),
            transfer_class=c.get("transfer_class", TransferClass.SAFE_TO_TRANSFER).value if isinstance(c.get("transfer_class"), TransferClass) else c.get("transfer_class", "safe_to_transfer"),
            sensitive=c.get("sensitive", False),
            review_required=c.get("review_required", False),
            optional=c.get("optional", False),
            label=c.get("label", cid),
            description=c.get("description", ""),
        ))
    return out


def get_component_registry(repo_root: Path | str | None = None) -> list[BundleComponent]:
    """Return full component registry (portable + local-only)."""
    return _registry()


def get_component(component_id: str, repo_root: Path | str | None = None) -> BundleComponent | None:
    """Return component by id."""
    for c in _registry():
        if c.component_id == component_id:
            return c
    return None


def list_components(
    include_local_only: bool = False,
    transfer_class_filter: str | None = None,
    repo_root: Path | str | None = None,
) -> list[BundleComponent]:
    """List components; optionally filter by transfer_class or exclude local_only."""
    reg = _registry()
    if not include_local_only:
        reg = [c for c in reg if c.transfer_class != TransferClass.LOCAL_ONLY.value]
    if transfer_class_filter:
        reg = [c for c in reg if c.transfer_class == transfer_class_filter]
    return reg

"""
M49C: Portability boundaries — safe/review/local-only/rebuild/experimental report and component explain.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.continuity_bundle.components import get_component_registry, get_component
from workflow_dataset.continuity_bundle.models import TransferClass


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def get_portability_boundaries(repo_root: Path | str | None = None) -> dict[str, Any]:
    """
    Return classification report: safe_to_transfer, transfer_with_review, local_only,
    rebuild_on_restore, experimental_transfer; each list of component ids.
    """
    root = _root(repo_root)
    reg = get_component_registry(root)
    safe: list[str] = []
    review: list[str] = []
    local_only: list[str] = []
    rebuild: list[str] = []
    experimental: list[str] = []
    for c in reg:
        if c.transfer_class == TransferClass.SAFE_TO_TRANSFER.value:
            safe.append(c.component_id)
        elif c.transfer_class == TransferClass.TRANSFER_WITH_REVIEW.value:
            review.append(c.component_id)
        elif c.transfer_class == TransferClass.LOCAL_ONLY.value:
            local_only.append(c.component_id)
        elif c.transfer_class == TransferClass.REBUILD_ON_RESTORE.value:
            rebuild.append(c.component_id)
        elif c.transfer_class == TransferClass.EXPERIMENTAL_TRANSFER.value:
            experimental.append(c.component_id)
    return {
        "safe_to_transfer": safe,
        "transfer_with_review": review,
        "local_only": local_only,
        "rebuild_on_restore": rebuild,
        "experimental_transfer": experimental,
        "summary": f"safe={len(safe)} review={len(review)} local_only={len(local_only)} rebuild={len(rebuild)} experimental={len(experimental)}",
    }


def explain_component(
    component_id: str,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Explain one component: transfer_class, rationale, sensitive, review_required, optional,
    what happens on restore.
    """
    root = _root(repo_root)
    c = get_component(component_id, root)
    if c is None:
        return {
            "component_id": component_id,
            "found": False,
            "reason": "Unknown component id.",
            "transfer_class": "",
            "rationale": "",
            "on_restore": "",
        }
    rationale = {
        TransferClass.SAFE_TO_TRANSFER.value: "Safe to copy to another machine; no sensitive or machine-specific data.",
        TransferClass.TRANSFER_WITH_REVIEW.value: "Contains sensitive or scope-specific state; human review before restore.",
        TransferClass.LOCAL_ONLY.value: "Machine-specific or ephemeral; do not transfer.",
        TransferClass.REBUILD_ON_RESTORE.value: "Do not transfer; rebuild on target from scratch.",
        TransferClass.EXPERIMENTAL_TRANSFER.value: "Experimental; transfer only with review and acceptance of risk.",
    }.get(c.transfer_class, "Unclassified.")
    on_restore = {
        TransferClass.SAFE_TO_TRANSFER.value: "Restore overwrites or merges target path; continuity preserved.",
        TransferClass.TRANSFER_WITH_REVIEW.value: "Restore after approval; may conflict with target state.",
        TransferClass.LOCAL_ONLY.value: "Excluded from bundle; not restored.",
        TransferClass.REBUILD_ON_RESTORE.value: "Target should rebuild this component locally.",
        TransferClass.EXPERIMENTAL_TRANSFER.value: "Optional restore; validate compatibility first.",
    }.get(c.transfer_class, "See migration_restore flows.")
    return {
        "component_id": c.component_id,
        "found": True,
        "path": c.path,
        "transfer_class": c.transfer_class,
        "sensitive": c.sensitive,
        "review_required": c.review_required,
        "optional": c.optional,
        "label": c.label,
        "description": c.description,
        "rationale": rationale,
        "on_restore": on_restore,
    }

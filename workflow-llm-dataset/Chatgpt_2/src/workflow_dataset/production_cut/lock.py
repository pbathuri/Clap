"""
M40B: Final vertical lock — choose primary deployment vertical, explain, define workflows and surfaces.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from workflow_dataset.production_cut.models import (
    ProductionCut,
    ChosenPrimaryVertical,
    SupportedWorkflowSet,
    RequiredTrustPosture,
    DefaultOperatingProfile,
    ProductionReadinessNote,
)
from workflow_dataset.production_cut.freeze import build_production_freeze
from workflow_dataset.production_cut.store import set_active_cut


def choose_primary_from_evidence(
    vertical_id: str,
    repo_root: str | None = None,
) -> ChosenPrimaryVertical | None:
    """
    Build ChosenPrimaryVertical for the given vertical_id using vertical_selection and vertical_packs.
    Returns None if vertical not found or pack missing.
    """
    from workflow_dataset.vertical_selection import (
        get_candidate,
        explain_vertical,
        get_scope_report,
    )
    from workflow_dataset.vertical_selection.surface_policies import (
        get_surface_policy_report,
        is_surface_experimental,
    )
    from workflow_dataset.vertical_packs.registry import get_curated_pack

    root = _root(repo_root)
    c = get_candidate(vertical_id, root)
    if not c:
        return None
    pack = get_curated_pack(vertical_id)
    if not pack:
        return None

    explain = explain_vertical(vertical_id, root)
    selection_reason = explain.get("strength_reason") or f"Vertical {vertical_id} selected for production cut."
    if explain.get("weakness_reason"):
        selection_reason += " " + explain["weakness_reason"]

    scope = get_scope_report(vertical_id)
    core = set(scope.get("core_surfaces", []))
    optional = set(scope.get("optional_surfaces", []))
    hidden = set(scope.get("hidden_or_non_core_surfaces", []))
    policy = get_surface_policy_report(vertical_id)
    blocked = set(policy.get("blocked_surfaces", []))
    non_core = list(hidden - blocked)
    excluded = list(blocked) + list(policy.get("discouraged_surfaces", []))

    workflow_ids = []
    if pack.core_workflow_path:
        workflow_ids = list(pack.core_workflow_path.workflow_ids)
    allowed_roles = [vertical_id.replace("_core", "").replace("_", " ")]
    allowed_modes = ["operator_mode", "calm"]
    if pack.recommended_workday:
        if pack.recommended_workday.operator_mode_usage:
            allowed_modes = [pack.recommended_workday.operator_mode_usage]

    return ChosenPrimaryVertical(
        vertical_id=c.vertical_id,
        label=c.label or pack.name,
        description=pack.description or c.description,
        selection_reason=selection_reason[:500],
        primary_workflow_ids=workflow_ids,
        allowed_roles=allowed_roles,
        allowed_modes=allowed_modes,
        non_core_surface_ids=non_core[:50],
        excluded_surface_ids=excluded[:50],
    )


def build_production_cut_for_vertical(
    vertical_id: str,
    cut_id: str | None = None,
    repo_root: str | None = None,
) -> ProductionCut | None:
    """
    Build a full ProductionCut for the given vertical_id (final lock + freeze).
    cut_id defaults to vertical_id + '_primary'. Returns None if vertical/pack missing.
    """
    chosen = choose_primary_from_evidence(vertical_id, repo_root)
    if not chosen:
        return None
    freeze = build_production_freeze(vertical_id, repo_root)
    if not freeze:
        return None

    from workflow_dataset.vertical_packs.registry import get_curated_pack
    pack = get_curated_pack(vertical_id)
    cid = cut_id or (vertical_id + "_primary")
    label = (pack.name if pack else vertical_id) + " (production cut)"

    supported_workflows = None
    required_trust = None
    default_profile = None
    if pack:
        if pack.core_workflow_path:
            supported_workflows = SupportedWorkflowSet(
                workflow_ids=list(pack.core_workflow_path.workflow_ids),
                path_id=pack.core_workflow_path.path_id,
                label=pack.core_workflow_path.label,
                description=pack.core_workflow_path.description or "",
            )
        if pack.trust_review_posture:
            required_trust = RequiredTrustPosture(
                trust_preset_id=pack.trust_review_posture.trust_preset_id,
                review_gates_default=list(pack.trust_review_posture.review_gates_default),
                audit_posture=pack.trust_review_posture.audit_posture,
                description=pack.trust_review_posture.description,
            )
        if pack.recommended_workday and pack.recommended_queue:
            default_profile = DefaultOperatingProfile(
                workday_preset_id=pack.recommended_workday.workday_preset_id,
                default_experience_profile_id=pack.default_experience_profile_id or "",
                queue_section_order=pack.recommended_queue.queue_section_order or [],
                operator_mode_usage=pack.recommended_workday.operator_mode_usage or "",
                role_operating_hint=pack.recommended_workday.role_operating_hint or "",
            )

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    readiness = ProductionReadinessNote(
        summary=f"Production cut for {chosen.label}; scope frozen.",
        blockers=[],
        warnings=[],
        last_updated_utc=now,
    )

    return ProductionCut(
        cut_id=cid,
        vertical_id=vertical_id,
        label=label,
        frozen_at_utc=now,
        chosen_vertical=chosen,
        included_surface_ids=freeze["included_surface_ids"],
        excluded_surface_ids=freeze["excluded_surface_ids"],
        quarantined_surface_ids=freeze["quarantined_surface_ids"],
        supported_workflows=supported_workflows,
        required_trust=required_trust,
        default_profile=default_profile,
        production_readiness_note=readiness,
    )


def lock_production_cut(
    vertical_id: str,
    cut_id: str | None = None,
    repo_root: str | None = None,
) -> ProductionCut | None:
    """
    Build production cut for vertical and persist as active cut. Also sets active vertical and active pack.
    Returns the cut or None.
    """
    cut = build_production_cut_for_vertical(vertical_id, cut_id=cut_id, repo_root=repo_root)
    if not cut:
        return None
    root = _root(repo_root)
    set_active_cut(cut, root)
    from workflow_dataset.vertical_selection import set_active_vertical_id
    from workflow_dataset.vertical_packs import set_active_pack
    set_active_vertical_id(vertical_id, root)
    set_active_pack(vertical_id, root)
    return cut


def explain_production_cut(cut: ProductionCut) -> dict[str, Any]:
    """Return explain dict for CLI/reports: why this vertical, what's in/out, defaults."""
    out: dict[str, Any] = {
        "cut_id": cut.cut_id,
        "vertical_id": cut.vertical_id,
        "label": cut.label,
        "frozen_at_utc": cut.frozen_at_utc,
        "selection_reason": "",
        "included_count": len(cut.included_surface_ids),
        "excluded_count": len(cut.excluded_surface_ids),
        "quarantined_count": len(cut.quarantined_surface_ids),
        "primary_workflow_ids": [],
        "default_workday": "",
        "default_experience": "",
        "trust_preset": "",
    }
    if cut.chosen_vertical:
        out["selection_reason"] = cut.chosen_vertical.selection_reason
        out["primary_workflow_ids"] = list(cut.chosen_vertical.primary_workflow_ids)
    if cut.default_profile:
        out["default_workday"] = cut.default_profile.workday_preset_id
        out["default_experience"] = cut.default_profile.default_experience_profile_id
    if cut.required_trust:
        out["trust_preset"] = cut.required_trust.trust_preset_id
    return out


def _root(repo_root: str | None) -> str | None:
    return repo_root

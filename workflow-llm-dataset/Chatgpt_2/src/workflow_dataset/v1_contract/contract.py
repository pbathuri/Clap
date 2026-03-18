"""
M50B: Build stable v1 contract from production cut and freeze.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.v1_contract.models import (
    StableV1Contract,
    V1CoreSurface,
    V1SupportedAdvancedSurface,
    QuarantinedExperimentalSurface,
    ExcludedSurface,
    StableWorkflowContract,
    SupportedOperatingPosture,
    SupportCommitmentNote,
)


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _surface_label(surface_id: str) -> str:
    try:
        from workflow_dataset.default_experience.surfaces import get_surface_by_id
        s = get_surface_by_id(surface_id)
        return s.label if s else surface_id.replace("_", " ").title()
    except Exception:
        return surface_id.replace("_", " ").title()


def build_stable_v1_contract(repo_root: Path | str | None = None) -> StableV1Contract:
    """
    Build the stable v1 contract from active production cut or default vertical freeze.
    Classifies surfaces into v1_core, v1_advanced, quarantined, excluded.
    """
    root = _root(repo_root)
    from workflow_dataset.production_cut.store import get_active_cut
    from workflow_dataset.production_cut.freeze import build_production_freeze
    from workflow_dataset.vertical_selection.scope_lock import get_core_surfaces, get_optional_surfaces

    cut = get_active_cut(root)
    vertical_id = "founder_operator"
    vertical_label = "Founder / Operator"
    frozen_at_utc = ""
    included_ids: list[str] = []
    excluded_ids: list[str] = []
    quarantined_ids: list[str] = []
    workflow_ids: list[str] = []
    path_id = ""
    path_label = ""
    path_description = ""
    trust_preset_id = ""
    review_gates: list[str] = []
    audit_posture = ""
    operator_mode_usage = ""
    posture_description = ""
    support_summary = "Stable v1: core and advanced surfaces supported; quarantined experimental; excluded out of scope."
    in_scope: list[str] = ["Core and advanced surfaces", "Supported workflows", "Migration continuity bundle and restore"]
    out_of_scope: list[str] = ["Quarantined experimental surfaces", "Excluded surfaces", "Unsupported workflows"]

    if cut:
        vertical_id = cut.vertical_id or vertical_id
        frozen_at_utc = cut.frozen_at_utc or ""
        included_ids = list(cut.included_surface_ids)
        excluded_ids = list(cut.excluded_surface_ids)
        quarantined_ids = list(cut.quarantined_surface_ids)
        if cut.chosen_vertical:
            vertical_label = cut.chosen_vertical.label or vertical_id
            workflow_ids = list(cut.chosen_vertical.primary_workflow_ids or [])
        if cut.supported_workflows:
            workflow_ids = workflow_ids or cut.supported_workflows.workflow_ids
            path_id = cut.supported_workflows.path_id or ""
            path_label = cut.supported_workflows.label or ""
            path_description = cut.supported_workflows.description or ""
        if cut.required_trust:
            trust_preset_id = cut.required_trust.trust_preset_id or ""
            review_gates = list(cut.required_trust.review_gates_default or [])
            audit_posture = cut.required_trust.audit_posture or ""
            posture_description = cut.required_trust.description or ""
        if cut.default_profile:
            operator_mode_usage = cut.default_profile.operator_mode_usage or ""
        if cut.production_readiness_note:
            support_summary = cut.production_readiness_note.summary or support_summary
    else:
        freeze = build_production_freeze(vertical_id, root)
        if freeze:
            included_ids = list(freeze.get("included_surface_ids", []))
            excluded_ids = list(freeze.get("excluded_surface_ids", []))
            quarantined_ids = list(freeze.get("quarantined_surface_ids", []))
        try:
            from workflow_dataset.vertical_packs.registry import get_curated_pack
            pack = get_curated_pack(vertical_id)
            if pack:
                vertical_label = getattr(pack, "label", vertical_id) or vertical_id
                workflow_ids = list(getattr(pack, "workflow_ids", []) or [])
        except Exception:
            pass

    core_ids = get_core_surfaces(vertical_id) if vertical_id else []
    optional_ids = get_optional_surfaces(vertical_id) if vertical_id else []
    core_set = set(core_ids)
    optional_set = set(optional_ids)

    v1_core: list[V1CoreSurface] = []
    v1_advanced: list[V1SupportedAdvancedSurface] = []
    for sid in included_ids:
        label = _surface_label(sid)
        if sid in core_set:
            v1_core.append(V1CoreSurface(surface_id=sid, label=label, rationale="Core surface for chosen vertical."))
        else:
            v1_advanced.append(V1SupportedAdvancedSurface(surface_id=sid, label=label, rationale="Supported advanced or optional surface."))

    quarantined: list[QuarantinedExperimentalSurface] = [
        QuarantinedExperimentalSurface(surface_id=sid, label=_surface_label(sid), reveal_rule="on_demand", rationale="Experimental; not in v1 supported set.")
        for sid in quarantined_ids
    ]
    excluded: list[ExcludedSurface] = [
        ExcludedSurface(surface_id=sid, label=_surface_label(sid), reason="out_of_scope")
        for sid in excluded_ids
    ]

    stable_workflow = StableWorkflowContract(
        workflow_ids=workflow_ids,
        path_id=path_id,
        label=path_label or f"Stable workflows for {vertical_id}",
        description=path_description or "Primary supported workflows for stable v1.",
        excluded_workflow_ids=[],
    )
    posture = SupportedOperatingPosture(
        trust_preset_id=trust_preset_id,
        review_gates_default=review_gates,
        audit_posture=audit_posture,
        operator_mode_usage=operator_mode_usage,
        description=posture_description or "Required trust and review posture for v1.",
    )
    support_note = SupportCommitmentNote(
        summary=support_summary,
        in_scope=in_scope,
        out_of_scope=out_of_scope,
        last_updated_utc=frozen_at_utc,
    )

    return StableV1Contract(
        contract_id="stable_v1_contract",
        vertical_id=vertical_id,
        vertical_label=vertical_label,
        frozen_at_utc=frozen_at_utc,
        v1_core_surfaces=v1_core,
        v1_advanced_surfaces=v1_advanced,
        quarantined_surfaces=quarantined,
        excluded_surfaces=excluded,
        stable_workflow_contract=stable_workflow,
        supported_operating_posture=posture,
        support_commitment_note=support_note,
        migration_support_expectation="Continuity bundle and migration restore supported for v1.",
        has_active_cut=cut is not None,
    )

"""
M48B: Role–scope bindings — effective surfaces and action classes from production_cut and trust.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.governance.models import RoleAuthorityBinding
from workflow_dataset.governance.roles import get_role
from workflow_dataset.governance.scope import resolve_scope, ScopeLevelId


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def get_effective_binding(
    role_id: str,
    scope_hint: str | None,
    repo_root: Path | str | None = None,
) -> RoleAuthorityBinding | None:
    """
    Effective binding for role at scope: surfaces and action classes, review/override, authority tier.
    Uses production_cut required_trust and default profile when available; else role defaults.
    """
    root = _root(repo_root)
    role = get_role(role_id)
    if role is None:
        return None
    scope = resolve_scope(scope_hint, root)
    if scope is None:
        scope_level = ScopeLevelId.PRODUCT_WIDE.value
        scope_id = ""
    else:
        scope_level = scope.level_id
        scope_id = scope.scope_id or ""

    # Cap authority by trust preset from production cut
    trust_preset_id = "supervised_operator"
    authority_tier_id = role.default_authority_tier_id
    try:
        from workflow_dataset.production_cut import get_active_cut
        cut = get_active_cut(root)
        if cut and getattr(cut, "required_trust", None):
            trust_preset_id = cut.required_trust.trust_preset_id or trust_preset_id
            from workflow_dataset.trust.presets import get_preset
            preset = get_preset(trust_preset_id)
            if preset and preset.max_authority_tier_id:
                from workflow_dataset.trust.tiers import get_tier
                tier = get_tier(preset.max_authority_tier_id)
                cap_order = tier.order if tier else 99
                role_tier = get_tier(role.default_authority_tier_id)
                role_order = role_tier.order if role_tier else 0
                if cap_order < role_order:
                    authority_tier_id = preset.max_authority_tier_id
    except Exception:
        pass

    # Effective surfaces: role allowed, minus forbidden; intersect with production cut included if available
    effective_surfaces = list(role.allowed_surface_ids) if role.allowed_surface_ids else []
    if not role.allowed_surface_ids:
        effective_surfaces = ["workspace_home", "day_status", "queue_summary", "continuity_carry_forward", "inbox"]
    for fid in role.forbidden_surface_ids:
        if fid in effective_surfaces:
            effective_surfaces.remove(fid)
    try:
        from workflow_dataset.production_cut import get_active_cut
        cut = get_active_cut(root)
        if cut and getattr(cut, "included_surface_ids", None):
            included = set(cut.included_surface_ids)
            effective_surfaces = [s for s in effective_surfaces if s in included]
    except Exception:
        pass

    # Effective action classes: role allowed minus forbidden, capped by tier
    effective_actions = list(role.allowed_action_classes)
    for a in role.forbidden_action_classes:
        if a in effective_actions:
            effective_actions.remove(a)
    try:
        from workflow_dataset.trust.tiers import get_tier
        tier = get_tier(authority_tier_id)
        if tier and tier.allowed_action_classes:
            effective_actions = [a for a in effective_actions if a in tier.allowed_action_classes]
    except Exception:
        pass

    review_required = role.may_review and not role.may_approve and scope_level in (
        ScopeLevelId.REVIEW_DOMAIN.value,
        ScopeLevelId.VERTICAL.value,
    )
    override_required = role.may_request_only and role.may_execute is False

    return RoleAuthorityBinding(
        role_id=role_id,
        scope_level=scope_level,
        scope_id=scope_id,
        effective_surface_ids=effective_surfaces,
        effective_action_classes=effective_actions,
        review_required=review_required,
        override_required=override_required,
        authority_tier_id=authority_tier_id,
        trust_preset_id=trust_preset_id,
    )

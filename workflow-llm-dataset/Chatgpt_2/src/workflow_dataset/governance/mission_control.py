"""
M48D: Mission control slice — active governance posture, role map, sensitive scopes, blocked attempts, next review.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.governance.roles import list_roles
from workflow_dataset.governance.bindings import get_effective_binding
from workflow_dataset.governance.scope import resolve_scope
from workflow_dataset.governance.check import can_role_perform_action
from workflow_dataset.governance.presets import get_active_preset


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def governance_slice(repo_root: Path | str | None = None) -> dict[str, Any]:
    """
    Additive mission-control slice for governance.
    Keys: active_governance_posture, current_role_map, most_sensitive_active_scopes,
    blocked_authority_attempts_count, next_recommended_governance_review.
    """
    root = _root(repo_root)
    scope = resolve_scope("vertical", root)
    scope_label = scope.label if scope else "product_wide"
    roles = list_roles()
    role_map = [{"role_id": r.role_id, "label": r.label, "tier": r.default_authority_tier_id} for r in roles]
    sensitive_scopes: list[str] = []
    try:
        from workflow_dataset.production_cut import get_active_cut
        cut = get_active_cut(root)
        if cut and getattr(cut, "required_trust", None):
            sensitive_scopes.append("vertical:" + getattr(cut, "vertical_id", ""))
        from workflow_dataset.review_domains.registry import list_domains
        for d in list_domains(root):
            did = getattr(d, "domain_id", "")
            if did:
                sensitive_scopes.append("review_domain:" + did)
    except Exception:
        pass
    if not sensitive_scopes:
        sensitive_scopes = ["product_wide"]
    blocked_count = 0
    for r in roles:
        res = can_role_perform_action(r.role_id, "commit_or_send", "vertical", None, root)
        if not res.allowed:
            blocked_count += 1
    preset = get_active_preset(root)
    active_preset_id = preset.preset_id if preset else "solo_operator"
    preset_implications = preset.implications[:5] if preset else []
    active_scope_template_id = preset.scope_template_id if preset else "solo_vertical"
    return {
        "active_governance_posture": scope_label,
        "active_governance_preset_id": active_preset_id,
        "preset_implications": preset_implications,
        "active_scope_template_id": active_scope_template_id,
        "current_role_map": role_map,
        "most_sensitive_active_scopes": sensitive_scopes[:5],
        "blocked_authority_attempts_count": blocked_count,
        "next_recommended_governance_review": "workflow-dataset governance roles",
    }

"""
M48B: Scope-bound governance — scope levels, precedence, resolve_scope, conflict.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.governance.models import AuthorityScope
from workflow_dataset.governance.models import ScopeLevelId

# Precedence: higher rank = more specific (wins in conflict)
SCOPE_LEVEL_RANK: dict[str, int] = {
    ScopeLevelId.PRODUCT_WIDE.value: 0,
    ScopeLevelId.VERTICAL.value: 1,
    ScopeLevelId.PROJECT.value: 2,
    ScopeLevelId.REVIEW_DOMAIN.value: 3,
    ScopeLevelId.WORKFLOW_ROUTINE.value: 4,
    ScopeLevelId.OPERATOR_MODE_ROUTINE.value: 5,
}

ScopeLevel = ScopeLevelId  # alias for __init__ export


def scope_precedence_rank(level_id: str) -> int:
    """Return precedence rank for scope level (higher = more specific)."""
    return SCOPE_LEVEL_RANK.get(level_id, -1)


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def resolve_scope(
    scope_hint: str | None,
    repo_root: Path | str | None = None,
) -> AuthorityScope | None:
    """
    Resolve scope from hint (product_wide | vertical | project:<id> | review_domain:<id> | workflow:<id> | operator_routine:<id>).
    Uses production_cut for vertical when hint is 'vertical' or empty.
    """
    root = _root(repo_root)
    hint = (scope_hint or "product_wide").strip().lower()
    if hint == "product_wide" or not hint:
        return AuthorityScope(
            level_id=ScopeLevelId.PRODUCT_WIDE.value,
            scope_id="",
            label="Product-wide",
            precedence_rank=scope_precedence_rank(ScopeLevelId.PRODUCT_WIDE.value),
            description="Applies to entire product.",
        )
    if hint == "vertical":
        try:
            from workflow_dataset.vertical_excellence.path_resolver import get_chosen_vertical_id
            vid = get_chosen_vertical_id(root)
            return AuthorityScope(
                level_id=ScopeLevelId.VERTICAL.value,
                scope_id=vid or "",
                label="Vertical: " + (vid or "—"),
                precedence_rank=scope_precedence_rank(ScopeLevelId.VERTICAL.value),
                description="Scoped to chosen vertical.",
            )
        except Exception:
            return AuthorityScope(
                level_id=ScopeLevelId.VERTICAL.value,
                scope_id="",
                label="Vertical",
                precedence_rank=scope_precedence_rank(ScopeLevelId.VERTICAL.value),
                description="Scoped to chosen vertical.",
            )
    if hint.startswith("project:"):
        pid = hint.split(":", 1)[1].strip()
        return AuthorityScope(
            level_id=ScopeLevelId.PROJECT.value,
            scope_id=pid,
            label="Project: " + pid,
            precedence_rank=scope_precedence_rank(ScopeLevelId.PROJECT.value),
            description="Scoped to project.",
        )
    if hint.startswith("review_domain:") or hint.startswith("domain:"):
        did = hint.split(":", 1)[1].strip()
        return AuthorityScope(
            level_id=ScopeLevelId.REVIEW_DOMAIN.value,
            scope_id=did,
            label="Review domain: " + did,
            precedence_rank=scope_precedence_rank(ScopeLevelId.REVIEW_DOMAIN.value),
            description="Scoped to review domain.",
        )
    if hint.startswith("workflow:") or hint.startswith("workflow_routine:"):
        wid = hint.split(":", 1)[1].strip()
        return AuthorityScope(
            level_id=ScopeLevelId.WORKFLOW_ROUTINE.value,
            scope_id=wid,
            label="Workflow: " + wid,
            precedence_rank=scope_precedence_rank(ScopeLevelId.WORKFLOW_ROUTINE.value),
            description="Scoped to workflow/routine.",
        )
    if hint.startswith("operator_routine:") or hint.startswith("operator_mode:"):
        oid = hint.split(":", 1)[1].strip() if ":" in hint else ""
        return AuthorityScope(
            level_id=ScopeLevelId.OPERATOR_MODE_ROUTINE.value,
            scope_id=oid,
            label="Operator routine: " + (oid or "default"),
            precedence_rank=scope_precedence_rank(ScopeLevelId.OPERATOR_MODE_ROUTINE.value),
            description="Scoped to operator-mode routine.",
        )
    return AuthorityScope(
        level_id=ScopeLevelId.PRODUCT_WIDE.value,
        scope_id="",
        label="Product-wide",
        precedence_rank=0,
        description="Default product-wide.",
    )

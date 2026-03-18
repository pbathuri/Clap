"""
M48L.1: Operator-facing guidance — what happens when a delegated scope is suspended or revoked, and what to do next.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.governed_operator.models import SuspensionRevocationGuidance, GovernedOperatorStatus
from workflow_dataset.governed_operator.store import get_scope, load_governed_state
from workflow_dataset.governed_operator.playbooks import get_reauthorization_playbook, get_playbook_for_situation


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def suspension_revocation_guidance(
    scope_id: str,
    repo_root: Path | str | None = None,
) -> SuspensionRevocationGuidance:
    """
    Return operator-facing guidance: what happens when this scope is suspended or revoked,
    what stops, what continues, and what to do next (including suggested playbook).
    """
    root = _root(repo_root)
    now = utc_now_iso()
    scope = get_scope(scope_id, repo_root=root)
    if not scope:
        return SuspensionRevocationGuidance(
            scope_id=scope_id,
            status="unknown",
            what_happens="Scope not found.",
            what_stops=[],
            what_continues=[],
            next_steps=["List scopes: workflow-dataset governed-operator scopes."],
            suggested_playbook_id="",
            suggested_playbook_label="",
            generated_at_utc=now,
        )
    state = load_governed_state(repo_root=root)
    revoked = state.get("revoked_scope_ids", [])
    suspended = state.get("suspended_scope_ids", [])
    reauth_needed = state.get("reauthorization_needed_scope_ids", [])

    label = scope.label or scope_id
    if scope_id in revoked:
        playbook = get_reauthorization_playbook("after_revoke") or get_playbook_for_situation("revoked")
        return SuspensionRevocationGuidance(
            scope_id=scope_id,
            status=GovernedOperatorStatus.REVOKED.value,
            what_happens="This delegated scope has been revoked. All operator-mode actions under this scope are no longer allowed. Work that depended on this scope will stop or require manual takeover.",
            what_stops=[f"All delegated work under scope '{label}'", "Routines and responsibilities tied to this scope", "Automatic execution under this scope"],
            what_continues=["Work under other active scopes", "Manual operator actions outside this scope"],
            next_steps=[
                "Run: workflow-dataset governed-operator explain --id " + scope_id,
                "To re-delegate: create a new scope with governed-operator scopes --create <new_id> --label ... --domain " + (scope.review_domain_id or "operator_routine") + " --role " + (scope.role_id or "operator"),
                "Optionally apply a preset: use --routine and a delegation preset (narrow_trusted_routine, supervised_operator, maintenance_only) when creating the new scope.",
            ],
            suggested_playbook_id=playbook.playbook_id if playbook else "after_revoke",
            suggested_playbook_label=playbook.label if playbook else "After revoke",
            generated_at_utc=now,
        )
    if scope_id in suspended:
        playbook = get_reauthorization_playbook("after_suspend") or get_playbook_for_situation("suspended")
        return SuspensionRevocationGuidance(
            scope_id=scope_id,
            status=GovernedOperatorStatus.SUSPENDED.value,
            what_happens="This delegated scope is suspended. Operator-mode actions under this scope are paused until you clear the suspension or revoke the scope. No new work runs under this scope until you decide.",
            what_stops=[f"New delegated work under scope '{label}'", "Continuation of loops/responsibilities under this scope until resumed"],
            what_continues=["Work under other active (non-suspended) scopes", "Manual operator actions"],
            next_steps=[
                "To resume: workflow-dataset governed-operator suspend --clear --id " + scope_id,
                "To revoke instead: workflow-dataset governed-operator revoke --id " + scope_id + " --reason <reason>",
                "Review why it was suspended; then run governed-operator explain --id " + scope_id + " for full guidance.",
            ],
            suggested_playbook_id=playbook.playbook_id if playbook else "after_suspend",
            suggested_playbook_label=playbook.label if playbook else "After suspend",
            generated_at_utc=now,
        )
    if scope_id in reauth_needed:
        playbook = get_reauthorization_playbook("reauthorization_needed") or get_playbook_for_situation("reauthorization_needed")
        return SuspensionRevocationGuidance(
            scope_id=scope_id,
            status=GovernedOperatorStatus.REAUTHORIZATION_NEEDED.value,
            what_happens="This scope has been marked as requiring reauthorization. Delegation under this scope should not be used until reauthorization is complete.",
            what_stops=[f"Use of scope '{label}' until reauthorization is complete"],
            what_continues=["Other active scopes"],
            next_steps=[
                "Complete the reauthorization flow for the review domain or policy that required it.",
                "Run: workflow-dataset governed-operator explain --id " + scope_id,
                "After reauthorization, clear the reauthorization-needed flag if supported, or suspend then clear suspension to reset.",
            ],
            suggested_playbook_id=playbook.playbook_id if playbook else "reauthorization_needed",
            suggested_playbook_label=playbook.label if playbook else "Reauthorization needed",
            generated_at_utc=now,
        )

    return SuspensionRevocationGuidance(
        scope_id=scope_id,
        status=GovernedOperatorStatus.ACTIVE.value,
        what_happens="This scope is active. Delegation is allowed within its boundaries.",
        what_stops=[],
        what_continues=[f"Delegated work under scope '{label}'"],
        next_steps=["Use governed-operator check --role <role> --routine <routine> to verify before running sensitive routines."],
        suggested_playbook_id="",
        suggested_playbook_label="",
        generated_at_utc=now,
    )

"""
M48L.1: Reauthorization playbooks — what to do after suspend, revoke, or when reauthorization is needed.
"""

from __future__ import annotations

from workflow_dataset.governed_operator.models import ReauthorizationPlaybook


def _builtin_playbooks() -> list[ReauthorizationPlaybook]:
    return [
        ReauthorizationPlaybook(
            playbook_id="after_suspend",
            label="After suspend",
            description="Resume or revoke a suspended delegated scope.",
            situation="suspended",
            steps=[
                "Review why the scope was suspended (policy, confidence, or manual).",
                "If safe to continue: run workflow-dataset governed-operator suspend --clear --id <scope_id>.",
                "If not safe: run workflow-dataset governed-operator revoke --id <scope_id> and create a new scope if needed.",
                "Re-run governed-operator check --role <role> --routine <routine> to confirm delegation is allowed.",
            ],
            when_to_use="Use when a scope is in suspended state and you need to either resume or permanently revoke.",
            outcome_note="Clearing suspension restores the scope to active; revoking removes it until a new scope is created.",
        ),
        ReauthorizationPlaybook(
            playbook_id="after_revoke",
            label="After revoke",
            description="Re-establish delegation after a scope was revoked.",
            situation="revoked",
            steps=[
                "Confirm the reason for revocation (unsafe state, conflict, or manual).",
                "Decide whether to re-delegate: if yes, create a new scope with governed-operator scopes --create <new_scope_id> --label ... --domain ... --role ...",
                "Optionally apply a delegation preset (narrow_trusted_routine, supervised_operator, maintenance_only) when creating the scope.",
                "Run governed-operator check --role <role> --routine <routine> --scope <new_scope_id> to verify.",
            ],
            when_to_use="Use when a scope has been revoked and you need to delegate again with the same or narrower boundaries.",
            outcome_note="Revoked scopes are not reused; create a new scope to delegate again.",
        ),
        ReauthorizationPlaybook(
            playbook_id="reauthorization_needed",
            label="Reauthorization needed",
            description="Complete reauthorization when a scope is marked reauthorization_needed.",
            situation="reauthorization_needed",
            steps=[
                "Review what triggered the reauthorization-needed flag (e.g. policy change, domain update).",
                "Complete any required approval or review in the review domain.",
                "Clear the reauthorization-needed flag when supported, or suspend then clear suspension to reset.",
                "Run governed-operator explain --id <scope_id> to confirm status.",
            ],
            when_to_use="Use when a scope is in reauthorization_needed state and you need to complete the reauthorization flow.",
            outcome_note="After reauthorization, the scope can return to active use.",
        ),
        ReauthorizationPlaybook(
            playbook_id="policy_breach",
            label="Policy breach",
            description="Respond to a suspension or revoke triggered by policy breach.",
            situation="policy_breach",
            steps=[
                "Identify which policy was breached (review domain, trust tier, or action boundary).",
                "Either narrow the scope (fewer routines or allowed actions) via governed-operator or create a new scope with a stricter preset (e.g. maintenance_only).",
                "If continuing: run suspend --clear only after confirming the breach is addressed.",
                "Consider using supervised_operator preset to reduce risk of future breach.",
            ],
            when_to_use="Use when suspension or revocation was due to policy breach and you need to resume safely.",
            outcome_note="Narrowing scope or switching to a stricter preset reduces future breach risk.",
        ),
    ]


_PLAYBOOKS: list[ReauthorizationPlaybook] | None = None


def list_reauthorization_playbooks() -> list[ReauthorizationPlaybook]:
    """Return all built-in reauthorization playbooks."""
    global _PLAYBOOKS
    if _PLAYBOOKS is None:
        _PLAYBOOKS = _builtin_playbooks()
    return list(_PLAYBOOKS)


def get_reauthorization_playbook(playbook_id: str) -> ReauthorizationPlaybook | None:
    """Return the playbook with the given playbook_id, or None."""
    for p in list_reauthorization_playbooks():
        if p.playbook_id == playbook_id:
            return p
    return None


def get_playbook_for_situation(situation: str) -> ReauthorizationPlaybook | None:
    """Return the first playbook whose situation matches (suspended, revoked, reauthorization_needed, policy_breach)."""
    situation = (situation or "").strip().lower()
    for p in list_reauthorization_playbooks():
        if p.situation == situation:
            return p
    return None

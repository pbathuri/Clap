"""
Supervised execution controller: propose → approve → execute only.
No hidden paths to real desktop actions.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from workflow_dataset.local_operator.execution import execute_action_proposal
from workflow_dataset.local_operator.state_store import load_operator_state


@dataclass
class ExecutionGateResult:
    """Outcome of pre-flight gating (before any adapter call)."""

    allowed: bool
    reason: str = ""


def gate_execution(
    action_id: str,
    *,
    approved: bool,
    repo_root: Path | str | None = None,
    require_registered_proposal: bool = True,
) -> ExecutionGateResult:
    """
    Enforce supervised flow:
    - explicit user approval required for actions with approval_requirement=explicit
    - optional match against proposals currently in operator state
    """
    if not approved:
        return ExecutionGateResult(False, "approval_required")

    state = load_operator_state(repo_root)
    proposals = list(state.get("action_proposals") or [])
    proposal = next((p for p in proposals if p.get("action_id") == action_id), None)

    if require_registered_proposal and not proposal:
        return ExecutionGateResult(False, "proposal_not_found")

    return ExecutionGateResult(True, "")


def run_supervised_execution(
    action_id: str,
    *,
    approved: bool,
    repo_root: Path | str | None = None,
    require_registered_proposal: bool = True,
) -> dict[str, Any]:
    """
    Single entry for CLI/UI: gate, then delegate to execute_action_proposal.

    Returns the same shape as execute_action_proposal, plus gate_reason on hard stops.
    """
    gate = gate_execution(
        action_id,
        approved=approved,
        repo_root=repo_root,
        require_registered_proposal=require_registered_proposal,
    )
    if not gate.allowed:
        if gate.reason == "approval_required":
            return {
                "success": False,
                "message": "Approval required (--approved)",
                "output": {},
                "log_record": {},
                "gate_reason": gate.reason,
            }
        return {
            "success": False,
            "message": f"Execution blocked: {gate.reason}",
            "output": {},
            "log_record": {},
            "gate_reason": gate.reason,
        }

    state = load_operator_state(repo_root)
    proposal = next(
        (p for p in (state.get("action_proposals") or []) if p.get("action_id") == action_id),
        None,
    )
    if not proposal:
        return {
            "success": False,
            "message": "Proposal not found",
            "output": {},
            "log_record": {},
            "gate_reason": "proposal_not_found",
        }

    return execute_action_proposal(proposal, repo_root=repo_root, approved=True)


class ExecutionController:
    """Thin OO surface for tests and future injection (e.g. mock adapters)."""

    def gate(self, action_id: str, *, approved: bool, repo_root: Path | str | None = None) -> ExecutionGateResult:
        return gate_execution(action_id, approved=approved, repo_root=repo_root)

    def execute(
        self,
        action_id: str,
        *,
        approved: bool,
        repo_root: Path | str | None = None,
    ) -> dict[str, Any]:
        return run_supervised_execution(
            action_id, approved=approved, repo_root=repo_root, require_registered_proposal=True
        )

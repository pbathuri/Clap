"""
M39E–M39H: Guided value paths — entry point, required surfaces, milestones, failure points.
"""

from __future__ import annotations

from workflow_dataset.vertical_packs.models import (
    CommonFailurePoint,
    FirstValuePath,
    FirstValuePathStep,
    SuccessMilestone,
)
from workflow_dataset.value_packs.golden_bundles import get_golden_bundle
from workflow_dataset.value_packs.first_run_flow import build_first_run_flow


# Standard milestone ids used across paths
MILESTONE_FIRST_RUN = "first_run_completed"
MILESTONE_RUNTIME_CHECK = "runtime_check_done"
MILESTONE_ONBOARD_APPROVALS = "onboard_approvals_done"
MILESTONE_FIRST_SIMULATE = "first_simulate_done"
MILESTONE_FIRST_REAL = "first_real_done"


def _milestones_for_founder_analyst_doc() -> list[SuccessMilestone]:
    return [
        SuccessMilestone(MILESTONE_FIRST_RUN, "First run", "Install/bootstrap completed", 1, "workflow-dataset package first-run", "first_run_completed"),
        SuccessMilestone(MILESTONE_RUNTIME_CHECK, "Runtime check", "Backends listed", 2, "workflow-dataset runtime backends", "runtime_check_done"),
        SuccessMilestone(MILESTONE_ONBOARD_APPROVALS, "Onboard approvals", "Approval status checked", 3, "workflow-dataset onboard status", "onboard_approvals_done"),
        SuccessMilestone(MILESTONE_FIRST_SIMULATE, "First simulate", "First simulate run completed", 4, "macro run --mode simulate", "first_simulate_done"),
        SuccessMilestone(MILESTONE_FIRST_REAL, "First real run", "First trusted-real run after approvals", 5, "jobs run --mode real", "first_real_done"),
    ]


def _failure_points_first_value() -> list[CommonFailurePoint]:
    return [
        CommonFailurePoint(1, "Install fails or dirs missing", "Run from repo root; check data/local exists", "workflow-dataset package first-run"),
        CommonFailurePoint(3, "No approval scope; real run blocked", "Add path_workspace or path_repo via onboard approve", "workflow-dataset onboard status"),
        CommonFailurePoint(4, "Simulate times out or errors", "Check runtime backends; try workflow-dataset runtime recommend", "workflow-dataset runtime backends"),
        CommonFailurePoint(5, "Real run rejected", "Ensure approvals granted; check trust cockpit", "workflow-dataset trust cockpit"),
    ]


def _failure_points_developer() -> list[CommonFailurePoint]:
    return [
        CommonFailurePoint(1, "Install fails", "Run from repo root", "workflow-dataset package first-run"),
        CommonFailurePoint(3, "path_repo not approved", "onboard approve with path_repo scope", "workflow-dataset onboard status"),
        CommonFailurePoint(4, "Replay demo fails", "Check task_spec path; use --mode simulate", "workflow-dataset jobs run --id replay_cli_demo --mode simulate"),
        CommonFailurePoint(5, "Apply confirm required", "Grant apply_confirm in approval registry", "workflow-dataset trust cockpit"),
    ]


def build_path_for_pack(pack_id: str) -> FirstValuePath | None:
    """
    Build first-value path for a value pack using golden bundle or first_run_flow.
    Returns FirstValuePath with entry_point, required_surface_ids, steps, milestones, suggested_next_actions, first_value_milestone_id, common_failure_points.
    """
    bundle = get_golden_bundle(pack_id)
    if bundle:
        steps = [
            FirstValuePathStep(
                s.step_number,
                s.title,
                s.command,
                s.what_user_sees or "",
                s.what_to_do_next or "",
                s.step_number in (1, 2, 3),
                _milestone_for_step(s.step_number),
            )
            for s in bundle.steps
        ]
        milestones = _milestones_for_founder_analyst_doc()
        if "developer" in pack_id.lower():
            failure_points = _failure_points_developer()
        else:
            failure_points = _failure_points_first_value()
        return FirstValuePath(
            path_id=f"{pack_id}_first_value",
            pack_id=pack_id,
            label=bundle.display_name,
            entry_point=bundle.steps[0].command if bundle.steps else "workflow-dataset package first-run",
            required_surface_ids=["workspace_home", "queue_summary", "approvals_urgent", "continuity_carry_forward"],
            steps=steps,
            milestones=milestones,
            suggested_next_actions=[
                "workflow-dataset workspace home --profile calm_default",
                "workflow-dataset value-packs first-run --id " + pack_id,
                "workflow-dataset day status",
                "workflow-dataset trust cockpit",
            ],
            first_value_milestone_id=MILESTONE_FIRST_SIMULATE,
            common_failure_points=failure_points,
        )
    flow = build_first_run_flow(pack_id)
    if flow.get("error") or not flow.get("steps"):
        return None
    steps = [
        FirstValuePathStep(
            s["step"],
            s["title"],
            s["command"],
            s.get("what_user_sees", ""),
            s.get("what_to_do_next", ""),
            s.get("run_read_only", False),
            _milestone_for_step(s["step"]),
        )
        for s in flow["steps"]
    ]
    return FirstValuePath(
        path_id=f"{pack_id}_first_value",
        pack_id=pack_id,
        label=f"First-value path for {pack_id}",
        entry_point=steps[0].command if steps else "workflow-dataset package first-run",
        required_surface_ids=["workspace_home", "queue_summary", "approvals_urgent"],
        steps=steps,
        milestones=_milestones_for_founder_analyst_doc(),
        suggested_next_actions=["workflow-dataset value-packs first-run --id " + pack_id, "workflow-dataset day status"],
        first_value_milestone_id=MILESTONE_FIRST_SIMULATE,
        common_failure_points=_failure_points_first_value(),
    )


def _milestone_for_step(step_number: int) -> str:
    m = {
        1: MILESTONE_FIRST_RUN,
        2: MILESTONE_RUNTIME_CHECK,
        3: MILESTONE_ONBOARD_APPROVALS,
        4: MILESTONE_FIRST_SIMULATE,
        5: MILESTONE_FIRST_REAL,
    }
    return m.get(step_number, "")

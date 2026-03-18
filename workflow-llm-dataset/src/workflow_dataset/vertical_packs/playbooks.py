"""
M39H.1: Vertical playbooks — common failure points by vertical, recovery paths, operator guidance when path stalls.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.vertical_packs.models import (
    RecoveryPath,
    RecoveryPathStep,
    VerticalPlaybook,
    VerticalPlaybookFailureEntry,
)


def _founder_operator_playbook() -> VerticalPlaybook:
    return VerticalPlaybook(
        playbook_id="founder_operator_playbook",
        curated_pack_id="founder_operator_core",
        label="Founder/operator vertical playbook",
        description="Common failure points and recovery paths for founder/operator first-value path.",
        failure_entries=[
            VerticalPlaybookFailureEntry(1, "Install fails or dirs missing", "Run from repo root; ensure data/local exists", "workflow-dataset package first-run", "recover_after_install"),
            VerticalPlaybookFailureEntry(3, "No approval scope; real run blocked", "Add path_workspace via onboard approve", "workflow-dataset onboard status", "recover_after_approval_block"),
            VerticalPlaybookFailureEntry(4, "Simulate times out or errors", "Check runtime backends; run runtime recommend", "workflow-dataset runtime backends", "recover_after_simulate_fail"),
            VerticalPlaybookFailureEntry(5, "Real run rejected", "Ensure approvals granted; check trust cockpit", "workflow-dataset trust cockpit", "recover_after_real_rejected"),
        ],
        recovery_paths=[
            RecoveryPath(
                "recover_after_install",
                "Recover after install failure",
                [
                    RecoveryPathStep(1, "workflow-dataset package first-run", "Re-run first-run from repo root"),
                    RecoveryPathStep(2, "workflow-dataset package install-check", "Verify install"),
                    RecoveryPathStep(3, "workflow-dataset vertical-packs first-value --id founder_operator_core", "Resume first-value path"),
                ],
                "first_run_completed",
            ),
            RecoveryPath(
                "recover_after_approval_block",
                "Recover after approval block",
                [
                    RecoveryPathStep(1, "workflow-dataset onboard status", "Check approval state"),
                    RecoveryPathStep(2, "workflow-dataset onboard approve", "Add path_workspace or path_repo scope"),
                    RecoveryPathStep(3, "workflow-dataset macro run --id morning_ops --mode simulate", "Retry first simulate"),
                ],
                "first_simulate_done",
            ),
            RecoveryPath(
                "recover_after_simulate_fail",
                "Recover after simulate failure",
                [
                    RecoveryPathStep(1, "workflow-dataset runtime backends", "Check backends"),
                    RecoveryPathStep(2, "workflow-dataset runtime recommend --task-class desktop_copilot", "Get recommended runtime"),
                    RecoveryPathStep(3, "workflow-dataset macro run --id morning_ops --mode simulate", "Retry simulate"),
                ],
                "first_simulate_done",
            ),
            RecoveryPath(
                "recover_after_real_rejected",
                "Recover after real run rejected",
                [
                    RecoveryPathStep(1, "workflow-dataset trust cockpit", "Check trust and approvals"),
                    RecoveryPathStep(2, "workflow-dataset onboard status", "Confirm approval scope"),
                    RecoveryPathStep(3, "workflow-dataset jobs run --id weekly_status_from_notes --mode real", "Retry real run"),
                ],
                "first_real_done",
            ),
        ],
        operator_guidance_stalled="Path stalled: run the escalation command for your step, then follow the recovery path to get back to first-value. Use vertical-packs recovery --id founder_operator_core --step <N> to see steps.",
        operator_commands_stalled=[
            "workflow-dataset vertical-packs recovery --id founder_operator_core --step 3",
            "workflow-dataset onboard status",
            "workflow-dataset trust cockpit",
        ],
    )


def _analyst_playbook() -> VerticalPlaybook:
    return VerticalPlaybook(
        playbook_id="analyst_playbook",
        curated_pack_id="analyst_core",
        label="Analyst vertical playbook",
        description="Common failure points and recovery for analyst first-value path.",
        failure_entries=[
            VerticalPlaybookFailureEntry(1, "Install fails", "Run from repo root", "workflow-dataset package first-run", "recover_after_install"),
            VerticalPlaybookFailureEntry(3, "Approval or data_export scope missing", "onboard approve with path_workspace and data_export", "workflow-dataset onboard status", "recover_after_approval_block"),
            VerticalPlaybookFailureEntry(4, "Simulate or job errors", "Check runtime; retry with weekly_status_from_notes --mode simulate", "workflow-dataset runtime backends", "recover_after_simulate_fail"),
            VerticalPlaybookFailureEntry(5, "Real run rejected", "Check trust cockpit and approval scope", "workflow-dataset trust cockpit", "recover_after_real_rejected"),
        ],
        recovery_paths=[
            RecoveryPath("recover_after_install", "Recover after install", [RecoveryPathStep(1, "workflow-dataset package first-run", "Re-run first-run"), RecoveryPathStep(2, "workflow-dataset vertical-packs first-value --id analyst_core", "Resume path")], "first_run_completed"),
            RecoveryPath("recover_after_approval_block", "Recover after approval block", [RecoveryPathStep(1, "workflow-dataset onboard status", "Check state"), RecoveryPathStep(2, "workflow-dataset onboard approve", "Add scopes"), RecoveryPathStep(3, "workflow-dataset jobs run --id weekly_status_from_notes --mode simulate", "Retry simulate")], "first_simulate_done"),
            RecoveryPath("recover_after_simulate_fail", "Recover after simulate fail", [RecoveryPathStep(1, "workflow-dataset runtime backends", "Check backends"), RecoveryPathStep(2, "workflow-dataset jobs run --id weekly_status_from_notes --mode simulate", "Retry")], "first_simulate_done"),
            RecoveryPath("recover_after_real_rejected", "Recover after real rejected", [RecoveryPathStep(1, "workflow-dataset trust cockpit", "Check trust"), RecoveryPathStep(2, "workflow-dataset jobs run --id weekly_status_from_notes --mode real", "Retry real")], "first_real_done"),
        ],
        operator_guidance_stalled="Path stalled: check approval and data_export scope; run recovery for your step. Use vertical-packs recovery --id analyst_core --step <N>.",
        operator_commands_stalled=["workflow-dataset vertical-packs recovery --id analyst_core --step 3", "workflow-dataset onboard status"],
    )


def _developer_playbook() -> VerticalPlaybook:
    return VerticalPlaybook(
        playbook_id="developer_playbook",
        curated_pack_id="developer_core",
        label="Developer vertical playbook",
        description="Common failure points and recovery for developer first-value path.",
        failure_entries=[
            VerticalPlaybookFailureEntry(1, "Install fails", "Run from repo root", "workflow-dataset package first-run", "recover_after_install"),
            VerticalPlaybookFailureEntry(3, "path_repo not approved", "onboard approve with path_repo scope", "workflow-dataset onboard status", "recover_after_approval_block"),
            VerticalPlaybookFailureEntry(4, "Replay demo fails", "Check task_spec path; use --mode simulate", "workflow-dataset jobs run --id replay_cli_demo --mode simulate", "recover_after_simulate_fail"),
            VerticalPlaybookFailureEntry(5, "Apply confirm required", "Grant apply_confirm in approval registry", "workflow-dataset trust cockpit", "recover_after_real_rejected"),
        ],
        recovery_paths=[
            RecoveryPath("recover_after_install", "Recover after install", [RecoveryPathStep(1, "workflow-dataset package first-run", "Re-run"), RecoveryPathStep(2, "workflow-dataset vertical-packs first-value --id developer_core", "Resume")], "first_run_completed"),
            RecoveryPath("recover_after_approval_block", "Recover after path_repo block", [RecoveryPathStep(1, "workflow-dataset onboard status", "Check"), RecoveryPathStep(2, "workflow-dataset onboard approve", "Add path_repo"), RecoveryPathStep(3, "workflow-dataset jobs run --id replay_cli_demo --mode simulate", "Retry simulate")], "first_simulate_done"),
            RecoveryPath("recover_after_simulate_fail", "Recover after replay fail", [RecoveryPathStep(1, "workflow-dataset runtime recommend --task-class codebase_task", "Check runtime"), RecoveryPathStep(2, "workflow-dataset jobs run --id replay_cli_demo --mode simulate", "Retry")], "first_simulate_done"),
            RecoveryPath("recover_after_real_rejected", "Recover after apply rejected", [RecoveryPathStep(1, "workflow-dataset trust cockpit", "Check apply_confirm"), RecoveryPathStep(2, "workflow-dataset jobs run --id replay_cli_demo --mode real", "Retry real")], "first_real_done"),
        ],
        operator_guidance_stalled="Path stalled: ensure path_repo and apply_confirm; run recovery for your step. vertical-packs recovery --id developer_core --step <N>.",
        operator_commands_stalled=["workflow-dataset vertical-packs recovery --id developer_core --step 3", "workflow-dataset trust cockpit"],
    )


def _document_worker_playbook() -> VerticalPlaybook:
    return VerticalPlaybook(
        playbook_id="document_worker_playbook",
        curated_pack_id="document_worker_core",
        label="Document worker vertical playbook",
        description="Common failure points and recovery for document worker first-value path.",
        failure_entries=[
            VerticalPlaybookFailureEntry(1, "Install fails", "Run from repo root", "workflow-dataset package first-run", "recover_after_install"),
            VerticalPlaybookFailureEntry(3, "path_workspace not approved", "onboard approve with path_workspace", "workflow-dataset onboard status", "recover_after_approval_block"),
            VerticalPlaybookFailureEntry(4, "Simulate or job errors", "Check runtime; retry weekly_status_from_notes simulate", "workflow-dataset runtime backends", "recover_after_simulate_fail"),
            VerticalPlaybookFailureEntry(5, "Real run rejected", "Check trust and path_workspace", "workflow-dataset trust cockpit", "recover_after_real_rejected"),
        ],
        recovery_paths=[
            RecoveryPath("recover_after_install", "Recover after install", [RecoveryPathStep(1, "workflow-dataset package first-run", "Re-run"), RecoveryPathStep(2, "workflow-dataset vertical-packs first-value --id document_worker_core", "Resume")], "first_run_completed"),
            RecoveryPath("recover_after_approval_block", "Recover after approval block", [RecoveryPathStep(1, "workflow-dataset onboard status", "Check"), RecoveryPathStep(2, "workflow-dataset onboard approve", "Add path_workspace"), RecoveryPathStep(3, "workflow-dataset jobs run --id weekly_status_from_notes --mode simulate", "Retry")], "first_simulate_done"),
            RecoveryPath("recover_after_simulate_fail", "Recover after simulate fail", [RecoveryPathStep(1, "workflow-dataset runtime backends", "Check"), RecoveryPathStep(2, "workflow-dataset jobs run --id weekly_status_from_notes --mode simulate", "Retry")], "first_simulate_done"),
            RecoveryPath("recover_after_real_rejected", "Recover after real rejected", [RecoveryPathStep(1, "workflow-dataset trust cockpit", "Check"), RecoveryPathStep(2, "workflow-dataset jobs run --id weekly_status_from_notes --mode real", "Retry")], "first_real_done"),
        ],
        operator_guidance_stalled="Path stalled: add path_workspace if needed; run recovery for your step. vertical-packs recovery --id document_worker_core --step <N>.",
        operator_commands_stalled=["workflow-dataset vertical-packs recovery --id document_worker_core --step 3", "workflow-dataset onboard status"],
    )


BUILTIN_VERTICAL_PLAYBOOKS: list[VerticalPlaybook] = [
    _founder_operator_playbook(),
    _analyst_playbook(),
    _developer_playbook(),
    _document_worker_playbook(),
]


def get_playbook_for_vertical(curated_pack_id: str) -> VerticalPlaybook | None:
    """Return vertical playbook for a curated pack id."""
    for p in BUILTIN_VERTICAL_PLAYBOOKS:
        if p.curated_pack_id == curated_pack_id:
            return p
    return None


def get_recovery_path_for_failure(playbook: VerticalPlaybook | None, step_index: int) -> RecoveryPath | None:
    """Return recovery path for a failure at step_index (from playbook failure_entries)."""
    if not playbook:
        return None
    recovery_path_id = ""
    for e in playbook.failure_entries:
        if e.step_index == step_index:
            recovery_path_id = e.recovery_path_id
            break
    if not recovery_path_id:
        return None
    for r in playbook.recovery_paths:
        if r.recovery_path_id == recovery_path_id:
            return r
    return None


def get_operator_guidance_when_stalled(
    curated_pack_id: str,
    blocked_step_index: int,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Return stronger operator guidance when curated path stalls at blocked_step_index.
    Keys: playbook_id, guidance, commands, recovery_path (dict or None), failure_entry (symptom, remediation_hint, escalation_command).
    """
    playbook = get_playbook_for_vertical(curated_pack_id)
    if not playbook:
        return {
            "playbook_id": "",
            "guidance": "Run vertical-packs first-value --id " + curated_pack_id + " and retry the suggested step.",
            "commands": ["workflow-dataset vertical-packs progress"],
            "recovery_path": None,
            "failure_entry": {},
        }
    failure_entry: dict[str, Any] = {}
    for e in playbook.failure_entries:
        if e.step_index == blocked_step_index:
            failure_entry = {"step_index": e.step_index, "symptom": e.symptom, "remediation_hint": e.remediation_hint, "escalation_command": e.escalation_command}
            break
    recovery = get_recovery_path_for_failure(playbook, blocked_step_index)
    return {
        "playbook_id": playbook.playbook_id,
        "guidance": playbook.operator_guidance_stalled,
        "commands": list(playbook.operator_commands_stalled),
        "recovery_path": recovery.to_dict() if recovery else None,
        "failure_entry": failure_entry,
    }


def list_vertical_playbook_ids() -> list[str]:
    """Return curated_pack_ids that have a playbook (for CLI list)."""
    return [p.curated_pack_id for p in BUILTIN_VERTICAL_PLAYBOOKS]

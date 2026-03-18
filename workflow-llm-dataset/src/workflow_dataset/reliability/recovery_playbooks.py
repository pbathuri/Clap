"""
M30E–M30H: Recovery playbooks — broken pack, failed upgrade, missing runtime, blocked approval, stuck project/agent, invalid workspace.
"""

from __future__ import annotations

from typing import Any

from workflow_dataset.reliability.models import RecoveryCase


RECOVERY_CASES: list[RecoveryCase] = [
    RecoveryCase(
        case_id="broken_pack_state",
        name="Broken or incompatible pack",
        when_to_use="Pack fails to load, behavior resolution errors, or pack is marked incompatible.",
        steps_guide=[
            "Run: workflow-dataset packs list (or workflow-dataset kits list) to see installed packs.",
            "Identify the pack causing errors from logs or reliability report (subsystem: packs).",
            "Run: workflow-dataset packs suspend --id <pack_id> to disable the pack without uninstall.",
            "If needed, run: workflow-dataset packs uninstall --id <pack_id> (or kits equivalent).",
            "Re-run reliability: workflow-dataset reliability run --id pack_install_behavior_query.",
        ],
        related_subsystems=["packs", "runtime_mesh"],
    ),
    RecoveryCase(
        case_id="failed_upgrade",
        name="Failed upgrade or migration",
        when_to_use="Install check fails after upgrade, or migration reports errors.",
        steps_guide=[
            "Run: workflow-dataset package install-check (or equivalent install check CLI) to see missing prereqs.",
            "Review migration_hints from template/workflow validation if applicable.",
            "Fix missing prerequisites or revert to last known-good install if possible.",
            "Run: workflow-dataset reliability run --id golden_first_run to validate install path.",
            "If blocked, run: workflow-dataset recovery guide --case failed_upgrade for full steps.",
        ],
        related_subsystems=["install", "distribution"],
    ),
    RecoveryCase(
        case_id="missing_runtime_capability",
        name="Missing runtime capability",
        when_to_use="Behavior resolution or workspace command query fails due to missing runtime.",
        steps_guide=[
            "Run: workflow-dataset reliability run --id pack_install_behavior_query to see failure step.",
            "Ensure required packs and runtime mesh are installed (workflow-dataset packs list, runtime mesh status if available).",
            "Check workspace and shell integration; ensure active work context can be built.",
            "Re-run the golden path after fixing runtime or pack activation.",
        ],
        related_subsystems=["runtime_mesh", "workspace", "packs"],
    ),
    RecoveryCase(
        case_id="blocked_approval_policy",
        name="Blocked approval or policy mode",
        when_to_use="Approval registry missing or policy blocks execution; operator cannot proceed.",
        steps_guide=[
            "Run: workflow-dataset trust status (or trust cockpit) to see approval readiness.",
            "Create or fix approval registry if missing (see onboarding/trust docs).",
            "Review human_policy / approval gates; defer or approve items as needed.",
            "Re-run: workflow-dataset reliability run --id review_inbox_approve_progress.",
        ],
        related_subsystems=["trust", "inbox", "human_policy"],
    ),
    RecoveryCase(
        case_id="stuck_project_session_agent",
        name="Stuck project/session/agent loop",
        when_to_use="Project is stalled, replan needed, or agent loop not advancing.",
        steps_guide=[
            "Run: workflow-dataset progress board (or equivalent) to see stalled/replan-needed projects.",
            "Run: workflow-dataset recovery suggest (no --case) to get matched playbook from progress.recovery.",
            "Follow operator_intervention and agent_next_step from the matched playbook.",
            "Optionally run: workflow-dataset reliability run --id project_plan_approve_simulate after unblocking.",
        ],
        related_subsystems=["planner", "progress", "session", "executor"],
    ),
    RecoveryCase(
        case_id="invalid_workspace_state",
        name="Invalid active workspace state",
        when_to_use="Workspace context fails to build, or active work context is invalid.",
        steps_guide=[
            "Run: workflow-dataset workspace home (or equivalent) to verify workspace areas.",
            "Check data/local/workspace (or configured workspace dir) exists and is readable.",
            "Fix or reset workspace state; ensure at least one valid area/section exists.",
            "Re-run: workflow-dataset reliability run --id pack_install_behavior_query (includes workspace_command_query step).",
        ],
        related_subsystems=["workspace"],
    ),
]


def list_recovery_cases() -> list[str]:
    """Return list of recovery case IDs."""
    return [c.case_id for c in RECOVERY_CASES]


def get_recovery_case(case_id: str) -> RecoveryCase | None:
    """Return recovery case by id."""
    for c in RECOVERY_CASES:
        if c.case_id == case_id:
            return c
    return None


def suggest_recovery(
    case_id: str | None = None,
    subsystem: str | None = None,
    outcome: str | None = None,
) -> dict[str, Any]:
    """
    Suggest recovery: if case_id given, return that case; else infer from subsystem/outcome.
    Returns { case_id, name, when_to_use, steps_guide, related_subsystems }.
    """
    if case_id:
        c = get_recovery_case(case_id)
        if c:
            return {
                "case_id": c.case_id,
                "name": c.name,
                "when_to_use": c.when_to_use,
                "steps_guide": c.steps_guide,
                "related_subsystems": c.related_subsystems,
            }
        return {"case_id": case_id, "error": f"Recovery case {case_id} not found"}

    # Auto-detect by subsystem
    if subsystem:
        for c in RECOVERY_CASES:
            if subsystem in c.related_subsystems:
                return {
                    "case_id": c.case_id,
                    "name": c.name,
                    "when_to_use": c.when_to_use,
                    "steps_guide": c.steps_guide,
                    "related_subsystems": c.related_subsystems,
                }
    # Default: stuck project (most generic)
    c = get_recovery_case("stuck_project_session_agent")
    if c:
        return {
            "case_id": c.case_id,
            "name": c.name,
            "when_to_use": c.when_to_use,
            "steps_guide": c.steps_guide,
            "related_subsystems": c.related_subsystems,
        }
    return {"error": "No recovery case suggested"}


def get_recovery_guide(case_id: str) -> str:
    """Return full recovery guide text for operator (when to use + steps)."""
    c = get_recovery_case(case_id)
    if not c:
        return f"Recovery case '{case_id}' not found. Use: workflow-dataset recovery suggest --case <case_id>"
    lines = [f"# {c.name} ({c.case_id})", "", "## When to use", c.when_to_use, "", "## Steps"]
    for i, step in enumerate(c.steps_guide, 1):
        lines.append(f"{i}. {step}")
    lines.extend(["", "Related subsystems: " + ", ".join(c.related_subsystems)])
    return "\n".join(lines)

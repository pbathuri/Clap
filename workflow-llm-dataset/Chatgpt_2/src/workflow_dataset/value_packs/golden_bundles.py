"""
M24H.1: Golden first-value bundles — pack-specific step definitions, sample input refs, expected outputs,
concrete job/routine/macro examples for founder, analyst, developer, document-worker.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class GoldenBundleStep:
    """Single step in a golden first-value bundle."""
    step_number: int
    title: str
    command: str
    sample_input_ref: str = ""   # relative path to demo asset or ""
    what_user_sees: str = ""
    what_to_do_next: str = ""


@dataclass
class GoldenFirstValueBundle:
    """Pack-specific golden first-value bundle: steps, sample inputs, expected outputs, example job/routine/macro."""
    pack_id: str
    bundle_id: str
    display_name: str
    description: str = ""
    steps: list[GoldenBundleStep] = field(default_factory=list)
    sample_input_refs: list[str] = field(default_factory=list)  # paths under value_packs/samples/
    expected_outputs: list[str] = field(default_factory=list)
    example_job_id: str = ""
    example_routine_id: str = ""
    example_macro_id: str = ""
    first_simulate_command: str = ""
    first_real_command: str = ""


def _founder_ops_bundle() -> GoldenFirstValueBundle:
    return GoldenFirstValueBundle(
        pack_id="founder_ops_plus",
        bundle_id="founder_ops_golden",
        display_name="Founder/operator golden first-value",
        description="Morning ops and weekly status from notes; simulate then real after approvals.",
        steps=[
            GoldenBundleStep(1, "Install / bootstrap", "workflow-dataset package first-run", "", "Dirs and install-check.", "Run profile bootstrap if prompted."),
            GoldenBundleStep(2, "Check runtime", "workflow-dataset runtime backends", "", "Backend list and status.", "Optional: runtime recommend --task-class desktop_copilot"),
            GoldenBundleStep(3, "Onboard approvals", "workflow-dataset onboard status", "", "Approval and bootstrap state.", "onboard approve when ready for real."),
            GoldenBundleStep(4, "First simulate run", "workflow-dataset macro run --id morning_ops --mode simulate", "founder_ops/morning_brief_notes.txt", "Simulated run; no writes.", "Then try first trusted-real run."),
            GoldenBundleStep(5, "First trusted-real candidate", "workflow-dataset jobs run --id weekly_status_from_notes --mode real", "founder_ops/weekly_status_input.md", "Real run after approvals.", "Check trust cockpit."),
        ],
        sample_input_refs=["founder_ops/morning_brief_notes.txt", "founder_ops/weekly_status_input.md", "example_notes.txt", "weekly_notes_sample.md"],
        expected_outputs=["Routine/job preview", "Plan run record", "Staging output in sandbox"],
        example_job_id="weekly_status_from_notes",
        example_routine_id="morning_ops",
        example_macro_id="morning_ops",
        first_simulate_command="workflow-dataset macro run --id morning_ops --mode simulate",
        first_real_command="workflow-dataset jobs run --id weekly_status_from_notes --mode real",
    )


def _analyst_research_bundle() -> GoldenFirstValueBundle:
    return GoldenFirstValueBundle(
        pack_id="analyst_research_plus",
        bundle_id="analyst_research_golden",
        display_name="Analyst/research golden first-value",
        description="Weekly status from notes and meeting brief; retrieval and local adapter; real after approvals.",
        steps=[
            GoldenBundleStep(1, "Install / bootstrap", "workflow-dataset package first-run", "", "Dirs and install-check.", "Bootstrap if prompted."),
            GoldenBundleStep(2, "Check runtime", "workflow-dataset runtime backends", "", "Backend list.", "Optional: runtime recommend."),
            GoldenBundleStep(3, "Onboard approvals", "workflow-dataset onboard status", "", "Approval state.", "onboard approve for real."),
            GoldenBundleStep(4, "First simulate run", "workflow-dataset jobs run --id weekly_status_from_notes --mode simulate", "analyst_research/weekly_findings.md", "Simulated job output.", "Confirm then add approvals."),
            GoldenBundleStep(5, "First trusted-real candidate", "workflow-dataset jobs run --id weekly_status_from_notes --mode real", "analyst_research/meeting_brief_input.txt", "Real run after approvals.", "Check trust cockpit."),
        ],
        sample_input_refs=["analyst_research/weekly_findings.md", "analyst_research/meeting_brief_input.txt", "example_notes.txt"],
        expected_outputs=["Job preview", "Run record", "Specialization memory update"],
        example_job_id="weekly_status_from_notes",
        example_routine_id="research_digest",
        example_macro_id="",
        first_simulate_command="workflow-dataset jobs run --id weekly_status_from_notes --mode simulate",
        first_real_command="workflow-dataset jobs run --id weekly_status_from_notes --mode real",
    )


def _developer_bundle() -> GoldenFirstValueBundle:
    return GoldenFirstValueBundle(
        pack_id="developer_plus",
        bundle_id="developer_golden",
        display_name="Developer golden first-value",
        description="Replay CLI demo in simulate; real only after path_repo and apply_confirm.",
        steps=[
            GoldenBundleStep(1, "Install / bootstrap", "workflow-dataset package first-run", "", "Dirs and install-check.", "Bootstrap if prompted."),
            GoldenBundleStep(2, "Check runtime", "workflow-dataset runtime backends", "", "Backend list.", "runtime recommend --task-class codebase_task."),
            GoldenBundleStep(3, "Onboard approvals", "workflow-dataset onboard status", "", "Approval state.", "Add path_repo and apply_confirm for real."),
            GoldenBundleStep(4, "First simulate run", "workflow-dataset jobs run --id replay_cli_demo --mode simulate", "developer/task_spec.md", "Task replay preview; no writes.", "Confirm pipeline."),
            GoldenBundleStep(5, "First trusted-real candidate", "workflow-dataset jobs run --id replay_cli_demo --mode real", "developer/replay_demo_notes.txt", "Real run after approvals.", "Check trust cockpit."),
        ],
        sample_input_refs=["developer/task_spec.md", "developer/replay_demo_notes.txt"],
        expected_outputs=["Task replay preview", "Simulate-only outcome"],
        example_job_id="replay_cli_demo",
        example_routine_id="",
        example_macro_id="",
        first_simulate_command="workflow-dataset jobs run --id replay_cli_demo --mode simulate",
        first_real_command="workflow-dataset jobs run --id replay_cli_demo --mode real",
    )


def _document_worker_bundle() -> GoldenFirstValueBundle:
    return GoldenFirstValueBundle(
        pack_id="document_worker_plus",
        bundle_id="document_worker_golden",
        display_name="Document worker golden first-value",
        description="Weekly status and doc workflow; local corpus; real after path_workspace approval.",
        steps=[
            GoldenBundleStep(1, "Install / bootstrap", "workflow-dataset package first-run", "", "Dirs and install-check.", "Bootstrap if prompted."),
            GoldenBundleStep(2, "Check runtime", "workflow-dataset runtime backends", "", "Backend list.", "Optional: runtime recommend."),
            GoldenBundleStep(3, "Onboard approvals", "workflow-dataset onboard status", "", "Approval state.", "onboard approve for real."),
            GoldenBundleStep(4, "First simulate run", "workflow-dataset jobs run --id weekly_status_from_notes --mode simulate", "document_worker/doc_outline.md", "Simulated job output.", "Confirm then add approvals."),
            GoldenBundleStep(5, "First trusted-real candidate", "workflow-dataset jobs run --id weekly_status_from_notes --mode real", "document_worker/weekly_digest_input.md", "Real run after approvals.", "Check trust cockpit."),
        ],
        sample_input_refs=["document_worker/doc_outline.md", "document_worker/weekly_digest_input.md", "weekly_notes_sample.md"],
        expected_outputs=["Job preview", "Run record"],
        example_job_id="weekly_status_from_notes",
        example_routine_id="doc_review",
        example_macro_id="",
        first_simulate_command="workflow-dataset jobs run --id weekly_status_from_notes --mode simulate",
        first_real_command="workflow-dataset jobs run --id weekly_status_from_notes --mode real",
    )


BUILTIN_GOLDEN_BUNDLES: list[GoldenFirstValueBundle] = [
    _founder_ops_bundle(),
    _analyst_research_bundle(),
    _developer_bundle(),
    _document_worker_bundle(),
]


def get_golden_bundle(pack_id: str) -> GoldenFirstValueBundle | None:
    """Return the golden first-value bundle for a value pack, or None."""
    for b in BUILTIN_GOLDEN_BUNDLES:
        if b.pack_id == pack_id:
            return b
    return None


def list_golden_bundle_pack_ids() -> list[str]:
    """Return pack ids that have a golden bundle."""
    return [b.pack_id for b in BUILTIN_GOLDEN_BUNDLES]

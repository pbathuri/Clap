"""
M24B: Built-in value pack definitions. Five verticals: founder/operator, analyst, developer, document worker, operations/logistics.
"""

from __future__ import annotations

from workflow_dataset.value_packs.models import ValuePack, FirstValueStep

# Default first-value sequence template: bootstrap → runtime → onboard → first simulate → first trusted-real candidate
def _default_sequence(pack_id: str, first_simulate_cmd: str, first_real_cmd: str) -> list[FirstValueStep]:
    return [
        FirstValueStep(1, "Install / bootstrap", "workflow-dataset package first-run", "Dirs created; install-check result; onboarding status.", "Run profile bootstrap if prompted.", False),
        FirstValueStep(2, "Check runtime", "workflow-dataset runtime backends", "Available backends and status.", "Optional: workflow-dataset runtime recommend --task-class desktop_copilot", True),
        FirstValueStep(3, "Onboard approvals", "workflow-dataset onboard status", "Current approval status and bootstrap state.", "Run onboard approve after adding paths/scopes if you want real execution.", True),
        FirstValueStep(4, "First simulate run", first_simulate_cmd, "Simulated output; no writes. Run record in data/local/copilot/runs or job_packs.", "Confirm pipeline; then add approvals and try first trusted-real run.", False),
        FirstValueStep(5, "First trusted-real candidate", first_real_cmd, "Only after approvals. Real run writes/executes per approval scope.", "Check trust cockpit; run workflow-dataset trust cockpit before real.", False),
    ]


BUILTIN_VALUE_PACKS: list[ValuePack] = [
    ValuePack(
        pack_id="founder_ops_plus",
        name="Founder / operator value pack",
        description="Light ops, reporting, stakeholder updates. Simulate-first; then real with approvals. Immediately useful for founders and small-team operators.",
        target_field="operations",
        target_job_family="founder",
        starter_kit_id="founder_ops_starter",
        domain_pack_id="founder_ops",
        recommended_profile_defaults={"field": "operations", "job_family": "founder"},
        recommended_runtime_task_class="desktop_copilot",
        recommended_model_class="general_chat_reasoning",
        recommended_external_capability_classes=[],
        recommended_job_ids=["weekly_status_from_notes", "weekly_status"],
        recommended_routine_ids=["morning_reporting", "morning_ops", "weekly_review"],
        recommended_macro_ids=["morning_ops"],
        first_simulate_only_workflow="morning_ops",
        first_trusted_real_candidate="weekly_status_from_notes",
        first_value_sequence=_default_sequence(
            "founder_ops_plus",
            "workflow-dataset macro run --id morning_ops --mode simulate",
            "workflow-dataset jobs run --id weekly_status_from_notes --mode real",
        ),
        benchmark_trust_notes="Benchmark: ops_reporting_core. Trust: simulate-only until approval registry and path scopes set.",
        approvals_likely_needed=["path_workspace", "apply_confirm"],
        expected_outputs=["Routine/job preview", "Plan run record", "Staging output in sandbox"],
        simulate_only_summary="All jobs and routines run in simulate by default; real mode after approvals.",
        sample_asset_paths=["example_notes.txt", "weekly_notes_sample.md", "founder_ops/morning_brief_notes.txt", "founder_ops/weekly_status_input.md"],
    ),
    ValuePack(
        pack_id="analyst_research_plus",
        name="Analyst / researcher value pack",
        description="Data analysis, literature, reports. Retrieval and local adapter preferred. Immediately useful for analysts and researchers.",
        target_field="research",
        target_job_family="analyst",
        starter_kit_id="analyst_starter",
        domain_pack_id="research_analyst",
        recommended_profile_defaults={"field": "research", "job_family": "analyst", "daily_task_style": "data_analysis"},
        recommended_runtime_task_class="desktop_copilot",
        recommended_model_class="general_chat_reasoning",
        recommended_external_capability_classes=[],
        recommended_job_ids=["weekly_status_from_notes", "weekly_status", "status_action_bundle", "meeting_brief_bundle"],
        recommended_routine_ids=["research_digest", "weekly_analysis"],
        recommended_macro_ids=[],
        first_simulate_only_workflow="weekly_status_from_notes",
        first_trusted_real_candidate="weekly_status_from_notes",
        first_value_sequence=_default_sequence(
            "analyst_research_plus",
            "workflow-dataset jobs run --id weekly_status_from_notes --mode simulate",
            "workflow-dataset jobs run --id weekly_status_from_notes --mode real",
        ),
        benchmark_trust_notes="Sensitive data; use retrieval and local adapter. Real mode after approvals.",
        approvals_likely_needed=["path_workspace", "apply_confirm", "data_export"],
        expected_outputs=["Job preview", "Run record", "Specialization memory update"],
        simulate_only_summary="Simulate validates job and adapters; real for export after approval.",
        sample_asset_paths=["example_notes.txt", "analyst_research/weekly_findings.md", "analyst_research/meeting_brief_input.txt"],
    ),
    ValuePack(
        pack_id="developer_plus",
        name="Developer / coding value pack",
        description="Code assistance, scaffolding, review. Simulate-first; apply only with confirm. Immediately useful for developers.",
        target_field="development",
        target_job_family="developer",
        starter_kit_id="developer_starter",
        domain_pack_id="coding_development",
        recommended_profile_defaults={"field": "development", "job_family": "developer", "daily_task_style": "code_first"},
        recommended_runtime_task_class="codebase_task",
        recommended_model_class="coding_agentic_coding",
        recommended_external_capability_classes=[],
        recommended_job_ids=["replay_cli_demo"],
        recommended_routine_ids=[],
        recommended_macro_ids=[],
        first_simulate_only_workflow="replay_cli_demo",
        first_trusted_real_candidate="replay_cli_demo",
        first_value_sequence=_default_sequence(
            "developer_plus",
            "workflow-dataset jobs run --id replay_cli_demo --mode simulate",
            "workflow-dataset jobs run --id replay_cli_demo --mode real",
        ),
        benchmark_trust_notes="Code changes require explicit apply; no auto-apply. Simulate-only for task replay.",
        approvals_likely_needed=["path_repo", "apply_confirm"],
        expected_outputs=["Task replay preview", "Simulate-only outcome"],
        simulate_only_summary="Coding jobs are simulate-only until path_repo and apply_confirm approved.",
        sample_asset_paths=["developer/task_spec.md", "developer/replay_demo_notes.txt"],
    ),
    ValuePack(
        pack_id="document_worker_plus",
        name="Document-heavy knowledge worker value pack",
        description="Long-form docs, knowledge bases, summarization. Local corpus and embeddings by default. Immediately useful for document-heavy roles.",
        target_field="document",
        target_job_family="knowledge",
        starter_kit_id="document_worker_starter",
        domain_pack_id="document_knowledge_worker",
        recommended_profile_defaults={"field": "document", "job_family": "writer", "daily_task_style": "document_heavy"},
        recommended_runtime_task_class="document_workflow",
        recommended_model_class="general_chat_reasoning",
        recommended_external_capability_classes=[],
        recommended_job_ids=["weekly_status_from_notes", "weekly_status", "meeting_brief_bundle"],
        recommended_routine_ids=["doc_review", "weekly_digest"],
        recommended_macro_ids=[],
        first_simulate_only_workflow="weekly_status_from_notes",
        first_trusted_real_candidate="weekly_status_from_notes",
        first_value_sequence=_default_sequence(
            "document_worker_plus",
            "workflow-dataset jobs run --id weekly_status_from_notes --mode simulate",
            "workflow-dataset jobs run --id weekly_status_from_notes --mode real",
        ),
        benchmark_trust_notes="Local corpus and embeddings only by default; real apply after approval.",
        approvals_likely_needed=["path_workspace", "apply_confirm"],
        expected_outputs=["Job preview", "Run record"],
        simulate_only_summary="Document jobs simulate first; real after workspace path approval.",
        sample_asset_paths=["weekly_notes_sample.md", "document_worker/doc_outline.md", "document_worker/weekly_digest_input.md"],
    ),
    ValuePack(
        pack_id="operations_logistics_plus",
        name="Operations / logistics value pack",
        description="Inventory, shipping, tracking, supplier communication. Ops and reporting workflows. Immediately useful for operations and logistics.",
        target_field="operations",
        target_job_family="operations",
        starter_kit_id="founder_ops_starter",
        domain_pack_id="logistics_ops",
        recommended_profile_defaults={"field": "operations", "job_family": "planner"},
        recommended_runtime_task_class="desktop_copilot",
        recommended_model_class="general_chat_reasoning",
        recommended_external_capability_classes=[],
        recommended_job_ids=["weekly_status_from_notes", "weekly_status", "status_action_bundle"],
        recommended_routine_ids=["morning_ops", "weekly_review"],
        recommended_macro_ids=["morning_ops"],
        first_simulate_only_workflow="weekly_status_from_notes",
        first_trusted_real_candidate="weekly_status",
        first_value_sequence=_default_sequence(
            "operations_logistics_plus",
            "workflow-dataset jobs run --id weekly_status_from_notes --mode simulate",
            "workflow-dataset jobs run --id weekly_status --mode real",
        ),
        benchmark_trust_notes="External systems; explicit approval for any API. Simulate-first for reporting.",
        approvals_likely_needed=["path_workspace", "apply_confirm", "external_api"],
        expected_outputs=["Job preview", "Run record", "Staging output"],
        simulate_only_summary="Reporting jobs simulate first; real and external_api after approvals.",
        sample_asset_paths=["example_notes.txt"],
    ),
]


def list_value_packs() -> list[str]:
    """Return list of value pack IDs."""
    return [p.pack_id for p in BUILTIN_VALUE_PACKS]


def get_value_pack(pack_id: str) -> ValuePack | None:
    """Return value pack by id, or None."""
    for p in BUILTIN_VALUE_PACKS:
        if p.pack_id == pack_id:
            return p
    return None

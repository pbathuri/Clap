"""
M23Y: Built-in starter kit definitions. Map to domain packs and job/routine IDs.
"""

from __future__ import annotations

from workflow_dataset.starter_kits.models import StarterKit, FirstValueFlow

BUILTIN_STARTER_KITS: list[StarterKit] = [
    StarterKit(
        kit_id="founder_ops_starter",
        name="Founder / operator starter",
        description="Light ops, reporting, stakeholder updates. Simulate-first; then real with approvals.",
        target_field="operations",
        target_job_family="founder",
        domain_pack_id="founder_ops",
        recommended_profile_defaults={"field": "operations", "job_family": "founder", "preferred_automation_degree": "simulate_first"},
        recommended_runtime_task_class="desktop_copilot",
        recommended_model_class="general_chat_reasoning",
        recommended_domain_pack_ids=["founder_ops"],
        recommended_job_ids=["weekly_status_from_notes", "weekly_status"],
        recommended_routine_ids=["morning_reporting", "morning_ops", "weekly_review"],
        first_simulate_only_workflow="morning_ops",
        first_value_flow=FirstValueFlow(
            first_run_command="workflow-dataset macro run --id morning_ops --mode simulate",
            what_user_gets_back="A simulated run of your morning routine: job steps and expected outputs (no writes).",
            why_useful="Confirms the pipeline works and shows what would run before enabling real mode.",
            what_to_do_next="Run 'workflow-dataset inbox' for daily digest; add approvals then try --mode real for trusted jobs.",
        ),
        trusted_real_eligibility_notes="Real mode after approval registry and path/scope approvals; start with simulate.",
        expected_outputs=["Preview of routine steps", "List of blocked items if any", "Plan run record in data/local/copilot/runs"],
        approvals_likely_needed=["path_workspace", "apply_confirm"],
    ),
    StarterKit(
        kit_id="analyst_starter",
        name="Analyst / researcher starter",
        description="Data analysis, literature, reports. Retrieval and local adapter preferred.",
        target_field="research",
        target_job_family="analyst",
        domain_pack_id="research_analyst",
        recommended_profile_defaults={"field": "research", "job_family": "analyst", "daily_task_style": "data_analysis"},
        recommended_runtime_task_class="desktop_copilot",
        recommended_model_class="general_chat_reasoning",
        recommended_domain_pack_ids=["research_analyst"],
        recommended_job_ids=["weekly_status_from_notes", "weekly_status", "status_action_bundle", "meeting_brief_bundle"],
        recommended_routine_ids=["research_digest", "weekly_analysis"],
        first_simulate_only_workflow="weekly_status_from_notes",
        first_value_flow=FirstValueFlow(
            first_run_command="workflow-dataset jobs run --id weekly_status_from_notes --mode simulate",
            what_user_gets_back="A simulate run of weekly status from notes: folder inspect and list (no writes).",
            why_useful="Validates job pack and adapters; safe way to see what the job would do.",
            what_to_do_next="Run 'workflow-dataset copilot recommend' for more jobs; add routine for research_digest if desired.",
        ),
        trusted_real_eligibility_notes="Sensitive data; use retrieval and local adapter; real mode after approvals.",
        expected_outputs=["Job preview output", "Run record in specialization memory"],
        approvals_likely_needed=["path_workspace", "apply_confirm", "data_export"],
    ),
    StarterKit(
        kit_id="developer_starter",
        name="Developer / coding-heavy starter",
        description="Code assistance, scaffolding, review. Simulate-first; apply only with confirm.",
        target_field="development",
        target_job_family="developer",
        domain_pack_id="coding_development",
        recommended_profile_defaults={"field": "development", "job_family": "developer", "daily_task_style": "code_first"},
        recommended_runtime_task_class="codebase_task",
        recommended_model_class="coding_agentic_coding",
        recommended_domain_pack_ids=["coding_development"],
        recommended_job_ids=["replay_cli_demo"],
        recommended_routine_ids=[],
        first_simulate_only_workflow="replay_cli_demo",
        first_value_flow=FirstValueFlow(
            first_run_command="workflow-dataset jobs run --id replay_cli_demo --mode simulate",
            what_user_gets_back="Replay of the CLI demo task in simulate mode (no code writes).",
            why_useful="Confirms coding-agent path and task replay; all code changes require explicit apply.",
            what_to_do_next="Run 'workflow-dataset runtime recommend --task-class codebase_task' for backend; add job packs for your repo.",
        ),
        trusted_real_eligibility_notes="Code changes require explicit apply; no auto-apply. Simulate-only for task replay.",
        expected_outputs=["Task replay preview", "Simulate-only outcome"],
        approvals_likely_needed=["path_repo", "apply_confirm"],
    ),
    StarterKit(
        kit_id="document_worker_starter",
        name="Document-heavy knowledge worker starter",
        description="Long-form docs, knowledge bases, summarization. Local corpus and embeddings by default.",
        target_field="document",
        target_job_family="knowledge",
        domain_pack_id="document_knowledge_worker",
        recommended_profile_defaults={"field": "document", "job_family": "writer", "daily_task_style": "document_heavy"},
        recommended_runtime_task_class="document_workflow",
        recommended_model_class="general_chat_reasoning",
        recommended_domain_pack_ids=["document_knowledge_worker"],
        recommended_job_ids=["weekly_status_from_notes", "weekly_status", "meeting_brief_bundle"],
        recommended_routine_ids=["doc_review", "weekly_digest"],
        first_simulate_only_workflow="weekly_status_from_notes",
        first_value_flow=FirstValueFlow(
            first_run_command="workflow-dataset jobs run --id weekly_status_from_notes --mode simulate",
            what_user_gets_back="Simulate run: inspect folder and list; no document writes.",
            why_useful="Validates setup and job; use retrieval/corpus for richer doc workflows after setup.",
            what_to_do_next="Run 'workflow-dataset inbox' for digest; build corpus and run embedding_refresh recipe for retrieval.",
        ),
        trusted_real_eligibility_notes="Local corpus and embeddings only by default; real apply after approval.",
        expected_outputs=["Job preview", "Run record"],
        approvals_likely_needed=["path_workspace", "apply_confirm"],
    ),
]


def list_kits() -> list[str]:
    """Return list of starter kit IDs."""
    return [k.kit_id for k in BUILTIN_STARTER_KITS]


def get_kit(kit_id: str) -> StarterKit | None:
    """Return starter kit by id, or None."""
    for k in BUILTIN_STARTER_KITS:
        if k.kit_id == kit_id:
            return k
    return None

"""
M51H.1: Demo user presets — bind role + workspace pack + staging checklist for a consistent first-run demo.
"""

from __future__ import annotations

from workflow_dataset.demo_onboarding.models import DemoUserPreset

DEFAULT_DEMO_USER_PRESET_ID = "investor_demo_primary"

DEMO_USER_PRESETS: dict[str, DemoUserPreset] = {
    "investor_demo_primary": DemoUserPreset(
        user_preset_id="investor_demo_primary",
        label="Primary investor demo (founder + Acme sample)",
        role_preset_id="founder_operator_demo",
        workspace_pack_id="acme_operator_default",
        investor_narrative=(
            "New operator plugs in after USB boot, picks founder path, ingests a tiny sample workspace "
            "that looks like weekly ops — then sees ready-to-assist with workspace home as first value."
        ),
        staging_checklist=[
            "Fresh machine or reset demo session: demo onboarding start --reset",
            "Apply user preset: demo onboarding user-preset --id investor_demo_primary",
            "Run bootstrap-memory (uses pack automatically): demo onboarding bootstrap-memory",
            "Show ready-state, then day preset + defaults as printed",
            "Optional: dry-run package first-run on USB image before live demo",
        ],
        operator_setup_commands=[
            "workflow-dataset demo onboarding staging-guide",
            "workflow-dataset demo onboarding user-preset --list",
        ],
    ),
    "investor_demo_documents": DemoUserPreset(
        user_preset_id="investor_demo_documents",
        label="Investor demo — document review path",
        role_preset_id="document_review_demo",
        workspace_pack_id="document_review_slice",
        investor_narrative="Same flow with document-heavy day preset and review-oriented sample files.",
        staging_checklist=[
            "demo onboarding start --reset",
            "demo onboarding user-preset --id investor_demo_documents",
            "demo onboarding bootstrap-memory",
            "demo onboarding ready-state",
        ],
        operator_setup_commands=[
            "workflow-dataset demo onboarding workspace-pack --list",
        ],
    ),
    "investor_demo_analyst": DemoUserPreset(
        user_preset_id="investor_demo_analyst",
        label="Investor demo — analyst follow-up path",
        role_preset_id="analyst_followup_demo",
        workspace_pack_id="analyst_followup_slice",
        investor_narrative="Queue/board-oriented narrative with sprint-style sample notes.",
        staging_checklist=[
            "demo onboarding start --reset",
            "demo onboarding user-preset --id investor_demo_analyst",
            "demo onboarding bootstrap-memory",
            "Highlight progress board as first value in ready-state",
        ],
        operator_setup_commands=[],
    ),
}


def get_demo_user_preset(user_preset_id: str) -> DemoUserPreset | None:
    return DEMO_USER_PRESETS.get(user_preset_id)


def list_demo_user_preset_ids() -> list[str]:
    return list(DEMO_USER_PRESETS.keys())


def get_default_demo_user_preset() -> DemoUserPreset:
    return DEMO_USER_PRESETS[DEFAULT_DEMO_USER_PRESET_ID]

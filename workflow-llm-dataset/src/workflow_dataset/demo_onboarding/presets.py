"""
M51E–M51H: Tightly scoped demo role presets. Default: founder_operator_demo.
"""

from __future__ import annotations

from workflow_dataset.demo_onboarding.models import RolePreset, TrustPostureSelection

DEFAULT_DEMO_PRESET_ID = "founder_operator_demo"

_TRUST_DEMO = TrustPostureSelection(
    posture_id="demo_conservative",
    label="Demo conservative",
    description="Simulate-first; approvals not auto-granted. Run onboard approve only when you want real execution.",
    simulate_first=True,
    approval_note="workflow-dataset onboard status  →  onboard approve",
)

ROLE_PRESETS: dict[str, RolePreset] = {
    "founder_operator_demo": RolePreset(
        preset_id="founder_operator_demo",
        label="Founder / operator (investor demo)",
        description="Ops reporting, daily priorities, inbox-style follow-ups. Best default for USB demo after boot.",
        vertical_pack_id="founder_operator_core",
        day_preset_id="founder_operator",
        default_experience_profile="calm_default",
        trust_posture=_TRUST_DEMO,
        enabled_surfaces_hint=["workspace home", "day status", "queue", "inbox"],
        recommended_first_value_command="workflow-dataset workspace home --profile calm_default",
    ),
    "document_review_demo": RolePreset(
        preset_id="document_review_demo",
        label="Document review",
        description="Focused on drafts, review queues, and calm document-heavy workday layout.",
        vertical_pack_id="founder_operator_core",
        day_preset_id="document_heavy",
        default_experience_profile="calm_default",
        trust_posture=_TRUST_DEMO,
        enabled_surfaces_hint=["workspace home", "drafts", "in-flow review"],
        recommended_first_value_command="workflow-dataset workspace home --profile calm_default",
    ),
    "analyst_followup_demo": RolePreset(
        preset_id="analyst_followup_demo",
        label="Analyst / project follow-up",
        description="Project board, follow-ups, and structured queue for recurring check-ins.",
        vertical_pack_id="founder_operator_core",
        day_preset_id="analyst",
        default_experience_profile="calm_default",
        trust_posture=_TRUST_DEMO,
        enabled_surfaces_hint=["progress board", "queue", "projects list"],
        recommended_first_value_command="workflow-dataset progress board",
    ),
}


def get_role_preset(preset_id: str) -> RolePreset | None:
    return ROLE_PRESETS.get(preset_id)


def list_role_preset_ids() -> list[str]:
    return list(ROLE_PRESETS.keys())


def get_default_role_preset() -> RolePreset:
    return ROLE_PRESETS[DEFAULT_DEMO_PRESET_ID]

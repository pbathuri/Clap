"""
M39E–M39H: Curated vertical pack registry — built-in packs and lookup.
"""

from __future__ import annotations

from workflow_dataset.vertical_packs.models import (
    CuratedVerticalPack,
    CoreWorkflowPath,
    RecommendedQueueProfile,
    RecommendedWorkdayProfile,
    RequiredSurfaces,
    TrustReviewPosture,
)
from workflow_dataset.vertical_packs.paths import build_path_for_pack
from workflow_dataset.workday.presets import (
    PRESET_FOUNDER_OPERATOR,
    PRESET_ANALYST,
    PRESET_DEVELOPER,
    PRESET_DOCUMENT_HEAVY,
)
from workflow_dataset.default_experience.profiles import (
    PROFILE_FOUNDER_CALM,
    PROFILE_ANALYST_CALM,
    PROFILE_DEVELOPER_CALM,
    PROFILE_DOCUMENT_CALM,
)


def _founder_operator_core() -> CuratedVerticalPack:
    path = build_path_for_pack("founder_ops_plus")
    return CuratedVerticalPack(
        pack_id="founder_operator_core",
        name="Founder / Operator (core)",
        description="Curated pack for founders and small-team operators: morning ops, weekly status, portfolio-first workday, supervised operator trust.",
        value_pack_id="founder_ops_plus",
        workday_preset_id=PRESET_FOUNDER_OPERATOR,
        default_experience_profile_id=PROFILE_FOUNDER_CALM,
        trust_review_posture=TrustReviewPosture(
            trust_preset_id="supervised_operator",
            review_gates_default=["before_real"],
            audit_posture="before_real",
            description="Human-in-the-loop; real run only after approval.",
        ),
        recommended_workday=RecommendedWorkdayProfile(
            workday_preset_id=PRESET_FOUNDER_OPERATOR,
            default_day_states=["startup", "review_and_approvals", "focus_work", "operator_mode", "wrap_up", "shutdown"],
            default_transition_after_startup="review_and_approvals",
            queue_review_emphasis="high",
            operator_mode_usage="preferred",
            role_operating_hint="Portfolio and approvals first; operator mode for delegated runs.",
        ),
        recommended_queue=RecommendedQueueProfile(
            queue_section_order=["approval_queue", "focus_ready", "review_ready", "operator_ready", "wrap_up"],
            calmness_default="calm",
            max_visible_sections=6,
            emphasis="high",
        ),
        core_workflow_path=CoreWorkflowPath(
            path_id="founder_ops_core_workflow",
            label="Founder ops core workflow",
            workflow_ids=["morning_ops", "weekly_status_from_notes", "weekly_status", "morning_reporting"],
            description="Morning ops and weekly status from notes; then reporting routines.",
        ),
        first_value_path=path,
        required_surfaces=RequiredSurfaces(
            required_surface_ids=["workspace_home", "day_status", "queue_summary", "approvals_urgent", "continuity_carry_forward"],
            optional_surface_ids=["mission_control", "review_studio", "automation_inbox", "trust_cockpit"],
            hidden_for_vertical=[],
        ),
        recommended_operator_bundle_id="founder_morning_ops",
        recommended_automation_settings={"allow_morning_continuity": True, "allow_resume_continuity": True},
    )


def _analyst_core() -> CuratedVerticalPack:
    path = build_path_for_pack("analyst_research_plus")
    return CuratedVerticalPack(
        pack_id="analyst_core",
        name="Analyst / Researcher (core)",
        description="Curated pack for analysts and researchers: weekly status, meeting brief, focus-first workday, supervised trust.",
        value_pack_id="analyst_research_plus",
        workday_preset_id=PRESET_ANALYST,
        default_experience_profile_id=PROFILE_ANALYST_CALM,
        trust_review_posture=TrustReviewPosture(
            trust_preset_id="supervised_operator",
            review_gates_default=["before_real", "data_export"],
            audit_posture="before_real",
            description="Sensitive data; real and export after approval.",
        ),
        recommended_workday=RecommendedWorkdayProfile(
            workday_preset_id=PRESET_ANALYST,
            default_day_states=["startup", "focus_work", "review_and_approvals", "wrap_up", "shutdown"],
            default_transition_after_startup="focus_work",
            queue_review_emphasis="medium",
            operator_mode_usage="rare",
            role_operating_hint="Focus work first; review when queue has items.",
        ),
        recommended_queue=RecommendedQueueProfile(
            queue_section_order=["focus_ready", "review_ready", "approval_queue", "wrap_up"],
            calmness_default="calm",
            max_visible_sections=5,
            emphasis="medium",
        ),
        core_workflow_path=CoreWorkflowPath(
            path_id="analyst_core_workflow",
            label="Analyst core workflow",
            workflow_ids=["weekly_status_from_notes", "meeting_brief_bundle", "research_digest", "weekly_analysis"],
            description="Weekly status and meeting brief; research digest and analysis.",
        ),
        first_value_path=path,
        required_surfaces=RequiredSurfaces(
            required_surface_ids=["workspace_home", "day_status", "queue_summary", "continuity_carry_forward"],
            optional_surface_ids=["review_studio", "mission_control", "trust_cockpit"],
            hidden_for_vertical=[],
        ),
        recommended_operator_bundle_id="",
        recommended_automation_settings={},
    )


def _developer_core() -> CuratedVerticalPack:
    path = build_path_for_pack("developer_plus")
    return CuratedVerticalPack(
        pack_id="developer_core",
        name="Developer (core)",
        description="Curated pack for developers: replay CLI demo, focus/operator workday, apply confirm and path_repo approvals.",
        value_pack_id="developer_plus",
        workday_preset_id=PRESET_DEVELOPER,
        default_experience_profile_id=PROFILE_DEVELOPER_CALM,
        trust_review_posture=TrustReviewPosture(
            trust_preset_id="supervised_operator",
            review_gates_default=["before_real", "path_repo", "apply_confirm"],
            audit_posture="before_real",
            description="Code changes require apply_confirm; path_repo scope.",
        ),
        recommended_workday=RecommendedWorkdayProfile(
            workday_preset_id=PRESET_DEVELOPER,
            default_day_states=["startup", "focus_work", "operator_mode", "review_and_approvals", "wrap_up", "shutdown"],
            default_transition_after_startup="focus_work",
            queue_review_emphasis="medium",
            operator_mode_usage="preferred",
            role_operating_hint="Focus or operator mode; review before wrap.",
        ),
        recommended_queue=RecommendedQueueProfile(
            queue_section_order=["focus_ready", "operator_ready", "review_ready", "wrap_up"],
            calmness_default="calm",
            max_visible_sections=5,
            emphasis="medium",
        ),
        core_workflow_path=CoreWorkflowPath(
            path_id="developer_core_workflow",
            label="Developer core workflow",
            workflow_ids=["replay_cli_demo"],
            description="Replay CLI demo in simulate then real after approvals.",
        ),
        first_value_path=path,
        required_surfaces=RequiredSurfaces(
            required_surface_ids=["workspace_home", "queue_summary", "approvals_urgent", "trust_cockpit"],
            optional_surface_ids=["mission_control", "review_studio"],
            hidden_for_vertical=[],
        ),
        recommended_operator_bundle_id="",
        recommended_automation_settings={},
    )


def _document_worker_core() -> CuratedVerticalPack:
    path = build_path_for_pack("document_worker_plus")
    return CuratedVerticalPack(
        pack_id="document_worker_core",
        name="Document worker (core)",
        description="Curated pack for document-heavy work: weekly status, doc review, artifacts and review first.",
        value_pack_id="document_worker_plus",
        workday_preset_id=PRESET_DOCUMENT_HEAVY,
        default_experience_profile_id=PROFILE_DOCUMENT_CALM,
        trust_review_posture=TrustReviewPosture(
            trust_preset_id="supervised_operator",
            review_gates_default=["before_real", "path_workspace"],
            audit_posture="before_real",
            description="Real run after path_workspace approval.",
        ),
        recommended_workday=RecommendedWorkdayProfile(
            workday_preset_id=PRESET_DOCUMENT_HEAVY,
            default_day_states=["startup", "focus_work", "review_and_approvals", "wrap_up", "shutdown"],
            default_transition_after_startup="focus_work",
            queue_review_emphasis="high",
            operator_mode_usage="rare",
            role_operating_hint="Documents and artifacts first; review queue regularly.",
        ),
        recommended_queue=RecommendedQueueProfile(
            queue_section_order=["focus_ready", "review_ready", "approval_queue", "wrap_up"],
            calmness_default="calm",
            max_visible_sections=5,
            emphasis="high",
        ),
        core_workflow_path=CoreWorkflowPath(
            path_id="document_worker_core_workflow",
            label="Document worker core workflow",
            workflow_ids=["weekly_status_from_notes", "doc_review"],
            description="Weekly status and doc review; local corpus.",
        ),
        first_value_path=path,
        required_surfaces=RequiredSurfaces(
            required_surface_ids=["workspace_home", "day_status", "queue_summary", "approvals_urgent", "continuity_carry_forward"],
            optional_surface_ids=["review_studio", "timeline", "mission_control"],
            hidden_for_vertical=[],
        ),
        recommended_operator_bundle_id="",
        recommended_automation_settings={},
    )


BUILTIN_CURATED_PACKS: list[CuratedVerticalPack] = [
    _founder_operator_core(),
    _analyst_core(),
    _developer_core(),
    _document_worker_core(),
]


def get_curated_pack(pack_id: str) -> CuratedVerticalPack | None:
    """Return curated vertical pack by id."""
    for p in BUILTIN_CURATED_PACKS:
        if p.pack_id == pack_id:
            return p
    return None


def list_curated_pack_ids() -> list[str]:
    """Return all built-in curated pack ids."""
    return [p.pack_id for p in BUILTIN_CURATED_PACKS]


def get_curated_pack_for_value_pack(value_pack_id: str) -> CuratedVerticalPack | None:
    """Return curated pack that wraps the given value pack id."""
    for p in BUILTIN_CURATED_PACKS:
        if p.value_pack_id == value_pack_id:
            return p
    return None

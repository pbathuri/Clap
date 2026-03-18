"""
M47E–M47H: Friction clusters — queue→action, review→decision, morning→first, resume→context, routine→execution.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.vertical_speed.models import (
    FrictionCluster,
    FrictionKind,
    RepeatedHandoff,
    SlowTransition,
    UnnecessaryBranch,
    SpeedUpCandidate,
    RepeatValueBottleneck,
)


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def build_friction_clusters(
    repo_root: Path | str | None = None,
) -> list[FrictionCluster]:
    """Build friction clusters for the vertical (handoff overhead, review detour, slow transition, etc.)."""
    root = _root(repo_root)
    clusters: list[FrictionCluster] = []

    # Queue → action handoff overhead
    clusters.append(FrictionCluster(
        cluster_id="queue_to_action_handoff",
        kind=FrictionKind.handoff_overhead,
        label="Queue to action handoff",
        description="Multiple steps from queue item to execution: queue view → select item → card/handoff → run.",
        repeated_handoffs=[
            RepeatedHandoff(
                handoff_id="queue_to_card",
                from_surface="queue view",
                to_surface="action card / handoff",
                description="Queue item to card accept then handoff target.",
                occurrence_count_estimate=10,
                suggested_single_step="workflow-dataset vertical-speed action-route --item <item_id>",
            ),
        ],
        impact_summary="4 steps typical; can reduce to 2 with route-to-action.",
        suggested_action="Use vertical-speed action-route for top queue item to get single command.",
    ))

    # Review → decision detour
    clusters.append(FrictionCluster(
        cluster_id="review_to_decision_detour",
        kind=FrictionKind.review_detour,
        label="Review to decision detour",
        description="Each review item opened separately; no grouped review path.",
        repeated_handoffs=[
            RepeatedHandoff(
                handoff_id="inbox_to_approval",
                from_surface="inbox list",
                to_surface="approval queue / review studio",
                description="Inbox item to approval or review surface.",
                occurrence_count_estimate=5,
                suggested_single_step="workflow-dataset inbox list then workflow-dataset review-studio open for batch",
            ),
        ],
        impact_summary="Multiple context switches per review session.",
        suggested_action="Use queue view --mode review to see review-ready items; consider grouped review when multiple items.",
    ))

    # Morning → first action (slow transition)
    clusters.append(FrictionCluster(
        cluster_id="morning_first_action_transition",
        kind=FrictionKind.slow_transition,
        label="Morning to first action",
        description="Startup or resume to first concrete action often has extra step (e.g. open morning brief then choose).",
        slow_transitions=[
            SlowTransition(
                transition_id="startup_to_first",
                from_mode="startup",
                to_mode="review_and_approvals or focus_work",
                description="After day start, transition to first productive action.",
                typical_actions=["day status", "continuity morning", "queue view"],
                shortcut_available=True,
                shortcut_command="workflow-dataset continuity morning  # then use first_action_command from brief",
            ),
        ],
        impact_summary="First action can be 2–3 steps; shortcut: use first_action_command from morning brief.",
        suggested_action="Run continuity morning and use the first_action_command in the brief.",
    ))

    # Resume → context (unnecessary branch if queue empty)
    clusters.append(FrictionCluster(
        cluster_id="resume_context_branch",
        kind=FrictionKind.unnecessary_branch,
        label="Resume context branch",
        description="Resume can suggest queue view even when queue empty; or multiple entry points for same next step.",
        unnecessary_branches=[
            UnnecessaryBranch(
                branch_id="inbox_vs_queue",
                trigger="Morning or resume",
                branch_description="Both inbox list and queue view show overlapping items; user may open both.",
                suggested_merge="Use queue view as single entry (includes inbox-derived items when unified queue is built).",
            ),
        ],
        impact_summary="Redundant entry points for same content.",
        suggested_action="Prefer queue view as single morning entry when queue is non-empty; else continuity morning first_action_command.",
    ))

    # Operator routine → execution (approval step)
    clusters.append(FrictionCluster(
        cluster_id="routine_approval_step",
        kind=FrictionKind.handoff_overhead,
        label="Routine approval step",
        description="Trusted routine still requires approve-then-run; no one-click for pre-approved routine.",
        repeated_handoffs=[
            RepeatedHandoff(
                handoff_id="routine_approve_run",
                from_surface="copilot or job list",
                to_surface="executor or supervised run",
                description="Select routine → approve → run.",
                occurrence_count_estimate=2,
                suggested_single_step="workflow-dataset copilot recommend then accept card with handoff_target prefill_command",
            ),
        ],
        impact_summary="Two steps for trusted routine; safety preserved.",
        suggested_action="Use action card with prefill_command for routine to reduce one click.",
    ))

    return clusters


def get_speed_up_candidates(
    repo_root: Path | str | None = None,
    limit: int = 10,
) -> list[SpeedUpCandidate]:
    """Derive speed-up candidates from friction clusters and workflows."""
    root = _root(repo_root)
    clusters = build_friction_clusters(repo_root=root)
    candidates: list[SpeedUpCandidate] = []

    for c in clusters:
        if c.cluster_id == "queue_to_action_handoff":
            candidates.append(SpeedUpCandidate(
                candidate_id="route_top_queue_item",
                label="Route top queue item to single action",
                description="Use action-route for highest-priority queue item to get one command.",
                workflow_id="queue_item_to_action",
                friction_cluster_id=c.cluster_id,
                route_to_action="workflow-dataset vertical-speed action-route",
                expected_step_reduction=2,
                priority="high",
            ))
        elif c.cluster_id == "morning_first_action_transition":
            candidates.append(SpeedUpCandidate(
                candidate_id="morning_first_command",
                label="Use morning brief first_action_command",
                description="Run continuity morning; use first_action_command from brief as single next step.",
                workflow_id="morning_entry_first_action",
                friction_cluster_id=c.cluster_id,
                route_to_action="workflow-dataset continuity morning",
                expected_step_reduction=1,
                priority="high",
            ))
        elif c.cluster_id == "review_to_decision_detour":
            candidates.append(SpeedUpCandidate(
                candidate_id="grouped_review_mode",
                label="Use queue view --mode review",
                description="See all review-ready items in one view; reduce context switches.",
                workflow_id="review_item_to_decision",
                friction_cluster_id=c.cluster_id,
                route_to_action="workflow-dataset queue view --mode review",
                expected_step_reduction=1,
                priority="medium",
            ))

    return candidates[:limit]


def get_repeat_value_bottlenecks(
    repo_root: Path | str | None = None,
) -> list[RepeatValueBottleneck]:
    """Identify repeat-value bottlenecks (blocked with no hint, missing prefilled default)."""
    root = _root(repo_root)
    bottlenecks: list[RepeatValueBottleneck] = []

    try:
        from workflow_dataset.unified_queue import build_unified_queue
        items = build_unified_queue(repo_root=root, limit=50)
        blocked = [i for i in items if getattr(i, "section_id", "") == "blocked" or getattr(i, "actionability_class", "").value == "blocked"]
        if blocked:
            top = blocked[0]
            bottlenecks.append(RepeatValueBottleneck(
                bottleneck_id="blocked_queue_no_hint",
                workflow_id="queue_item_to_action",
                label="Blocked queue item without recovery hint",
                description="One or more queue items are blocked; recovery path can be suggested.",
                recovery_hint="workflow-dataset recovery suggest --subsystem <from_item> or vertical-speed action-route --item " + getattr(top, "item_id", ""),
                prefilled_default_available=False,
            ))
    except Exception:
        pass

    bottlenecks.append(RepeatValueBottleneck(
        bottleneck_id="resume_no_prefill",
        workflow_id="continuity_resume_to_context",
        label="Resume first action not prefilled",
        description="First action command is in brief but not always one-click.",
        recovery_hint="workflow-dataset continuity morning returns first_action_command; use it as next step.",
        prefilled_default_available=True,
    ))

    return bottlenecks

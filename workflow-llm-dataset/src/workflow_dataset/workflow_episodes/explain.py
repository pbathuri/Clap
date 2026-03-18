"""
M33A–M33D: Explain episode, stage, and handoff gaps (human-readable).
M33D.1: Episode type, transition map, advance/stall explanations.
"""

from __future__ import annotations

from workflow_dataset.workflow_episodes.models import WorkflowEpisode, HandoffGapKind


def build_episode_explanation(episode: WorkflowEpisode) -> dict[str, str | list[str]]:
    """Build human-readable explanation of the episode (includes episode_type when set)."""
    out: dict[str, str | list[str]] = {
        "episode_id": episode.episode_id,
        "summary": f"Workflow episode with {len(episode.linked_activities)} linked activities.",
        "evidence": list(episode.evidence_summary),
        "project": "",
        "confidence": f"{episode.overall_confidence:.2f}",
        "episode_type": getattr(episode, "episode_type", "") or "unknown",
        "episode_type_evidence": list(getattr(episode, "episode_type_evidence", [])),
    }
    if episode.inferred_project:
        out["project"] = f"{episode.inferred_project.label} (confidence={episode.inferred_project.confidence:.2f})"
        out["evidence"] = list(episode.evidence_summary) + list(episode.inferred_project.evidence)
    return out


def build_stage_explanation(episode: WorkflowEpisode) -> dict[str, str | list[str]]:
    """Build human-readable stage explanation."""
    from workflow_dataset.workflow_episodes.stage_detection import infer_stage
    stage, evidence = infer_stage(episode)
    return {
        "stage": stage.value,
        "evidence": evidence,
        "summary": f"Current workflow stage: {stage.value}. Evidence: {', '.join(evidence)}",
    }


def build_handoff_gaps_explanation(
    episode: WorkflowEpisode,
    repo_root: str | None = None,
) -> dict[str, list[dict[str, str]] | int]:
    """Build human-readable handoff-gaps explanation."""
    from workflow_dataset.workflow_episodes.stage_detection import infer_handoff_gaps
    gaps = infer_handoff_gaps(episode, repo_root=repo_root)
    return {
        "gaps": [
            {
                "kind": g.kind.value,
                "summary": g.summary,
                "evidence": g.evidence,
                "suggested_action": g.suggested_action,
            }
            for g in gaps
        ],
        "count": len(gaps),
    }


def build_transition_map_output(episode: WorkflowEpisode) -> dict[str, str | list[dict[str, str]]]:
    """M33D.1: Build transition-map output (current_stage, next_stages, full map)."""
    from workflow_dataset.workflow_episodes.transition_map import build_transition_map_output as _build
    return _build(episode)


def build_advance_stall_explanation(episode: WorkflowEpisode) -> dict[str, list[str]]:
    """M33D.1: Build why the workflow has advanced or stalled (clearer explanations)."""
    from workflow_dataset.workflow_episodes.transition_map import build_advance_stall_explanation as _build
    return _build(episode)

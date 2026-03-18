"""
M33A–M33D: Workflow stage and handoff-gap detection — infer stage, next-step candidates, missing approval/artifact.
"""

from __future__ import annotations

from pathlib import Path
from collections import defaultdict

from workflow_dataset.workflow_episodes.models import (
    WorkflowEpisode,
    WorkflowStage,
    HandoffGap,
    HandoffGapKind,
    NextStepCandidate,
    WorkflowEpisodeType,
)


def infer_stage(episode: WorkflowEpisode) -> tuple[WorkflowStage, list[str]]:
    """
    Infer workflow stage from linked activities (activity_type mix and paths).
    Returns (stage, evidence list).
    """
    if not episode.linked_activities:
        return WorkflowStage.UNKNOWN, ["no_activities"]

    activity_types: list[str] = []
    paths: list[str] = []
    for a in episode.linked_activities:
        activity_types.append(a.activity_type or "")
        if a.path:
            paths.append(a.path.lower())

    type_counts: dict[str, int] = defaultdict(int)
    for t in activity_types:
        type_counts[t] += 1

    # Extension hints (from path)
    exts: list[str] = []
    for p in paths:
        if "." in p:
            exts.append(p.rsplit(".", 1)[-1].split("/")[0][:10])
    ext_counts: dict[str, int] = defaultdict(int)
    for e in exts:
        ext_counts[e] += 1

    evidence: list[str] = []
    # Drafting: file_snapshot, writing-like extensions (md, py, docx, etc.)
    writing_ext = {"md", "mdx", "txt", "py", "ts", "js", "doc", "docx", "rst"}
    writing_n = sum(ext_counts.get(e, 0) for e in writing_ext)
    if writing_n >= 2 and "file_snapshot" in type_counts:
        evidence.append(f"writing_extensions={writing_n} file_events")
        return WorkflowStage.DRAFTING, evidence

    # Review: pdf, review-like activity
    if ext_counts.get("pdf", 0) >= 1 or "review" in " ".join(activity_types).lower():
        evidence.append("pdf_or_review_activity")
        return WorkflowStage.REVIEW, evidence

    # Intake: few events, mixed or discovery-like
    if len(episode.linked_activities) <= 5 and not writing_n:
        evidence.append("few_activities_no_writing")
        return WorkflowStage.INTAKE, evidence

    # Execution/follow-up: terminal, run-like
    sources = [a.source for a in episode.linked_activities]
    if "terminal" in sources:
        evidence.append("terminal_activity")
        return WorkflowStage.EXECUTION_FOLLOWUP, evidence

    # Default: drafting if any file activity
    if type_counts.get("file_snapshot", 0) or paths:
        evidence.append("file_activity_default")
        return WorkflowStage.DRAFTING, evidence

    evidence.append("default_unknown")
    return WorkflowStage.UNKNOWN, evidence


def infer_handoff_gaps(
    episode: WorkflowEpisode,
    repo_root: Path | str | None = None,
) -> list[HandoffGap]:
    """
    Infer handoff gaps: missing_approval (from review_studio/supervised_loop), possible missing_artifact, likely_context_switch.
    """
    gaps: list[HandoffGap] = []
    root = Path(repo_root).resolve() if repo_root else None
    if root is None:
        try:
            from workflow_dataset.path_utils import get_repo_root
            root = Path(get_repo_root()).resolve()
        except Exception:
            root = Path.cwd().resolve()

    # Missing approval: approval queue has pending items
    try:
        from workflow_dataset.supervised_loop.store import load_queue
        items = load_queue(root)
        pending = [i for i in items if getattr(i, "status", "pending") == "pending"]
        if pending:
            gaps.append(
                HandoffGap(
                    kind=HandoffGapKind.MISSING_APPROVAL,
                    summary="Pending items in approval queue; review or approve to continue.",
                    evidence=[f"pending_count={len(pending)}"],
                    suggested_action="workflow-dataset review-studio inbox or agent-loop status",
                )
            )
    except Exception:
        pass

    # Stale: no recent activity (optional - if episode.updated_at is old)
    if episode.linked_activities:
        from workflow_dataset.utils.dates import utc_now_iso
        last_ts = episode.linked_activities[0].timestamp_utc
        if last_ts and episode.updated_at_utc and last_ts < episode.updated_at_utc[:19]:
            pass  # Has recent activity
        # Could add: if last activity > 15 min ago -> STALE_EPISODE

    return gaps


def infer_next_step_candidates(episode: WorkflowEpisode) -> list[NextStepCandidate]:
    """
    Infer likely next-step candidates (e.g. open review, switch to terminal, save/export).
    """
    candidates: list[NextStepCandidate] = []
    if not episode.linked_activities:
        return candidates

    stage, _ = infer_stage(episode)
    sources = {a.source for a in episode.linked_activities}

    if stage == WorkflowStage.DRAFTING and "terminal" not in sources:
        candidates.append(
            NextStepCandidate(
                label="Run or test in terminal",
                context="terminal",
                confidence=0.5,
                evidence=["stage=drafting", "no_terminal_activity_yet"],
            )
        )
    if stage == WorkflowStage.REVIEW:
        candidates.append(
            NextStepCandidate(
                label="Open review studio or approval queue",
                context="review_studio",
                confidence=0.6,
                evidence=["stage=review"],
            )
        )
    if stage == WorkflowStage.APPROVAL_DECISION or any(g.kind == HandoffGapKind.MISSING_APPROVAL for g in episode.handoff_gaps):
        candidates.append(
            NextStepCandidate(
                label="Check approval queue and approve or reject",
                context="approval_queue",
                confidence=0.8,
                evidence=["approval_needed"],
            )
        )

    return candidates


def infer_episode_type(episode: WorkflowEpisode) -> tuple[WorkflowEpisodeType, list[str]]:
    """
    M33D.1: Infer workflow episode type from linked activities and stage.
    Returns (episode_type, evidence list).
    """
    if not episode.linked_activities:
        return WorkflowEpisodeType.UNKNOWN, ["no_activities"]

    paths = [a.path.lower() for a in episode.linked_activities if a.path]
    sources = {a.source for a in episode.linked_activities}
    exts: list[str] = []
    for p in paths:
        if "." in p:
            exts.append(p.rsplit(".", 1)[-1].split("/")[0][:10].lower())
    ext_counts: dict[str, int] = defaultdict(int)
    for e in exts:
        ext_counts[e] += 1

    evidence: list[str] = []
    # Coding/debugging: code extensions + terminal
    code_ext = {"py", "ts", "tsx", "js", "jsx", "go", "rs", "rb", "java", "sh", "bash"}
    code_n = sum(ext_counts.get(e, 0) for e in code_ext)
    if (code_n >= 1 and "terminal" in sources) or code_n >= 3:
        evidence.append(f"code_extensions={code_n} terminal={bool(sources & {'terminal'})}")
        return WorkflowEpisodeType.CODING_DEBUGGING, evidence

    # Approval cycle: review stage + approval-related (infer from stage + gaps)
    stage, _ = infer_stage(episode)
    if stage == WorkflowStage.REVIEW or stage == WorkflowStage.APPROVAL_DECISION:
        if any(g.kind == HandoffGapKind.MISSING_APPROVAL for g in episode.handoff_gaps):
            evidence.append("stage=review_or_approval missing_approval")
            return WorkflowEpisodeType.APPROVAL_CYCLE, evidence

    # Document handoff: doc extensions, multiple files
    doc_ext = {"md", "mdx", "doc", "docx", "pdf", "txt", "rst"}
    doc_n = sum(ext_counts.get(e, 0) for e in doc_ext)
    if doc_n >= 2:
        evidence.append(f"doc_extensions={doc_n}")
        return WorkflowEpisodeType.DOCUMENT_HANDOFF, evidence

    # Research synthesis: pdf + md/txt
    if ext_counts.get("pdf", 0) >= 1 and (ext_counts.get("md", 0) or ext_counts.get("txt", 0)):
        evidence.append("pdf_with_md_or_txt")
        return WorkflowEpisodeType.RESEARCH_SYNTHESIS, evidence

    # Meeting follow-up: few activities, notes-like
    if len(episode.linked_activities) <= 8 and doc_n >= 1:
        evidence.append("few_activities_with_docs")
        return WorkflowEpisodeType.MEETING_FOLLOWUP, evidence

    evidence.append("default_unknown")
    return WorkflowEpisodeType.UNKNOWN, evidence

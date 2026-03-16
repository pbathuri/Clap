"""
M23L: Explain why a recommendation is relevant now. Uses work state and trigger evaluation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.context.work_state import build_work_state
from workflow_dataset.context.snapshot import load_snapshot
from workflow_dataset.context.triggers import evaluate_trigger_for_job, evaluate_trigger_for_routine
from workflow_dataset.copilot.recommendations import recommend_jobs


def explain_recommendation(
    recommendation_id: str,
    repo_root: Path | str | None = None,
    context_snapshot: str = "latest",
) -> dict[str, Any]:
    """
    Explain a recommendation by id. Loads recommendations (with optional context), finds rec by recommendation_id,
    then adds work-state summary and trigger results. Returns dict with explanation text and structured fields.
    """
    root = Path(repo_root).resolve() if repo_root else None
    work_state = load_snapshot(context_snapshot, root) if context_snapshot else None
    if work_state is None:
        work_state = build_work_state(root)

    recs = recommend_jobs(root, limit=100, context_snapshot=work_state)
    rec = next((r for r in recs if r.get("recommendation_id") == recommendation_id), None)
    if not rec:
        return {
            "error": f"Recommendation not found: {recommendation_id}",
            "recommendation_id": recommendation_id,
        }

    job_id = rec.get("job_pack_id")
    trigger_results = evaluate_trigger_for_job(job_id, work_state, root)

    lines = [
        f"# Recommendation: {recommendation_id}",
        "",
        f"**Job:** {job_id}",
        f"**Reason:** {rec.get('reason', '')}",
        f"**Mode allowed:** {rec.get('mode_allowed', '')}",
        f"**Timing context:** {rec.get('recommended_timing_context', '')}",
        "",
        "## Why now?",
    ]
    for r in trigger_results:
        status = "✓" if r.triggered else "—"
        lines.append(f"- {status} {r.trigger_type}: {r.reason}")
        if r.blocker:
            lines.append(f"  Blocker: {r.blocker}")
    if rec.get("blocking_issues"):
        lines.append("")
        lines.append("## Blocking issues")
        for b in rec["blocking_issues"]:
            lines.append(f"- {b}")
    lines.append("")
    lines.append("## Approvals")
    lines.append(f"Required: {rec.get('required_approvals', [])}")
    lines.append(f"Registry present in context: {work_state.approvals_file_exists}")

    return {
        "recommendation_id": recommendation_id,
        "job_pack_id": job_id,
        "reason": rec.get("reason"),
        "mode_allowed": rec.get("mode_allowed"),
        "why_now_evidence": rec.get("why_now_evidence", []),
        "context_trigger": rec.get("context_trigger", []),
        "trigger_results": [
            {"trigger_type": r.trigger_type, "triggered": r.triggered, "reason": r.reason, "blocker": r.blocker}
            for r in trigger_results
        ],
        "blocking_issues": rec.get("blocking_issues", []),
        "explanation_md": "\n".join(lines),
    }


def explain_recommendation_by_job(
    job_pack_id: str,
    repo_root: Path | str | None = None,
    context_snapshot: str = "latest",
) -> dict[str, Any]:
    """Explain why a job might be recommended now (even if not in current recommendation list)."""
    root = Path(repo_root).resolve() if repo_root else None
    work_state = load_snapshot(context_snapshot, root) if context_snapshot else None
    if work_state is None:
        work_state = build_work_state(root)

    trigger_results = evaluate_trigger_for_job(job_pack_id, work_state, root)
    lines = [
        f"# Job: {job_pack_id}",
        "",
        "## Context triggers",
    ]
    for r in trigger_results:
        status = "✓" if r.triggered else "—"
        lines.append(f"- {status} {r.trigger_type}: {r.reason}")
        if r.blocker:
            lines.append(f"  Blocker: {r.blocker}")

    return {
        "job_pack_id": job_pack_id,
        "trigger_results": [
            {"trigger_type": r.trigger_type, "triggered": r.triggered, "reason": r.reason, "blocker": r.blocker}
            for r in trigger_results
        ],
        "explanation_md": "\n".join(lines),
    }

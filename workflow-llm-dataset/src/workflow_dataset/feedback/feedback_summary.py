"""
M19: Aggregate feedback and write readable report.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.feedback.feedback_models import TrialFeedbackEntry, TrialSessionSummary
from workflow_dataset.feedback.feedback_store import load_feedback_entries, load_session_summaries


def aggregate_feedback(
    store_path: Path | str | None = None,
) -> dict[str, Any]:
    """Aggregate feedback entries and session summaries into a dict for reporting."""
    entries = load_feedback_entries(store_path)
    summaries = load_session_summaries(store_path)

    by_task: dict[str, list[TrialFeedbackEntry]] = {}
    for e in entries:
        by_task.setdefault(e.task_id or "unknown", []).append(e)

    usefulness = [e.usefulness_rating for e in entries if e.usefulness_rating > 0]
    trust = [e.trust_rating for e in entries if e.trust_rating > 0]
    outcome_completed = sum(1 for e in entries if (e.outcome_rating or "").lower() == "completed")
    outcome_partial = sum(1 for e in entries if (e.outcome_rating or "").lower() == "partial")
    outcome_failed = sum(1 for e in entries if (e.outcome_rating or "").lower() == "failed")

    confusion: list[str] = []
    failure: list[str] = []
    freeform: list[str] = []
    for e in entries:
        if e.confusion_points:
            confusion.append(e.confusion_points.strip())
        if e.failure_points:
            failure.append(e.failure_points.strip())
        if e.freeform_feedback:
            freeform.append(e.freeform_feedback.strip())

    return {
        "num_entries": len(entries),
        "num_sessions": len(summaries),
        "tasks_attempted": sum(s.tasks_attempted for s in summaries),
        "tasks_completed": sum(s.tasks_completed for s in summaries),
        "by_task": {k: len(v) for k, v in by_task.items()},
        "outcome_completed": outcome_completed,
        "outcome_partial": outcome_partial,
        "outcome_failed": outcome_failed,
        "avg_usefulness": sum(usefulness) / len(usefulness) if usefulness else 0.0,
        "avg_trust": sum(trust) / len(trust) if trust else 0.0,
        "confusion_points": confusion[:20],
        "failure_points": failure[:20],
        "freeform_samples": freeform[:15],
    }


def write_feedback_report(
    output_path: Path | str | None = None,
    store_path: Path | str | None = None,
) -> Path:
    """Write latest_feedback_report.md summarizing sessions, tasks, usefulness, failures, recommendation."""
    store = Path(store_path) if store_path else Path("data/local/trials")
    out = Path(output_path) if output_path else store / "latest_feedback_report.md"
    out.parent.mkdir(parents=True, exist_ok=True)

    agg = aggregate_feedback(store)

    lines = [
        "# Trial feedback report",
        "",
        f"**Feedback entries:** {agg['num_entries']}",
        f"**Sessions:** {agg['num_sessions']}",
        f"**Tasks attempted (from summaries):** {agg['tasks_attempted']}",
        f"**Tasks completed:** {agg['tasks_completed']}",
        "",
        "## Outcomes",
        "",
        f"- Completed: {agg['outcome_completed']}",
        f"- Partial: {agg['outcome_partial']}",
        f"- Failed: {agg['outcome_failed']}",
        "",
        "## Ratings (1–5)",
        "",
        f"- Avg usefulness: {agg['avg_usefulness']:.2f}",
        f"- Avg trust: {agg['avg_trust']:.2f}",
        "",
        "## By task",
        "",
    ]
    for task_id, count in sorted(agg["by_task"].items()):
        lines.append(f"- **{task_id}**: {count} feedback entries")
    lines.append("")
    if agg["confusion_points"]:
        lines.append("## Confusion points (sample)")
        lines.append("")
        for c in agg["confusion_points"][:10]:
            lines.append(f"- {c[:200]}")
        lines.append("")
    if agg["failure_points"]:
        lines.append("## Failure points (sample)")
        lines.append("")
        for f in agg["failure_points"][:10]:
            lines.append(f"- {f[:200]}")
        lines.append("")
    if agg["freeform_samples"]:
        lines.append("## Freeform feedback (sample)")
        lines.append("")
        for s in agg["freeform_samples"][:8]:
            lines.append(f"- {s[:300]}")
        lines.append("")
    lines.append("## Recommendation")
    lines.append("")
    if agg["num_entries"] == 0:
        lines.append("- No feedback yet. Run trial tasks and record feedback, then re-run aggregate.")
    elif agg["outcome_failed"] > agg["outcome_completed"] and agg["num_entries"] >= 3:
        lines.append("- **Refine internally:** Failure rate high; fix friction before more users.")
    elif agg["avg_usefulness"] >= 3.0 and agg["outcome_completed"] >= 2:
        lines.append("- **Continue friendly trial** or **expand to narrow private pilot** if trust and consistency hold.")
    else:
        lines.append("- **Refine internally:** Gather more feedback or improve flows before expanding.")
    lines.append("")

    out.write_text("\n".join(lines), encoding="utf-8")
    return out

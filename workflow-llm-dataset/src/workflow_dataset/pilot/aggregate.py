"""
M21: Pilot aggregation — combine session logs and feedback into recurring blockers, warnings, degraded-mode frequency, recommendations.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from workflow_dataset.pilot.session_log import list_sessions, load_session
from workflow_dataset.pilot.feedback_capture import load_feedback, list_feedback_files
from workflow_dataset.pilot.session_models import PilotSessionRecord, PilotFeedbackRecord

DEFAULT_PILOT_DIR = Path("data/local/pilot")
AGGREGATE_JSON = "aggregate_report.json"
AGGREGATE_MD = "aggregate_report.md"


def _pilot_root(pilot_dir: Path | str | None = None) -> Path:
    return Path(pilot_dir) if pilot_dir else DEFAULT_PILOT_DIR


def aggregate_sessions(
    pilot_dir: Path | str | None = None,
    session_limit: int = 100,
) -> dict[str, Any]:
    """
    Aggregate all or recent sessions and feedback into a structured report.
    Returns dict: recurring_blockers, warning_counts, degraded_count, sessions_count,
    operator_friction, user_value_wins, recommendation_summary, sessions[], feedback_by_session.
    """
    root = _pilot_root(pilot_dir)
    sessions = list_sessions(pilot_dir, limit=session_limit)
    blocker_counter: Counter[str] = Counter()
    warning_counter: Counter[str] = Counter()
    degraded_count = 0
    disposition_counts: Counter[str] = Counter()
    operator_friction: list[str] = []
    user_quotes: list[str] = []
    usefulness_scores: list[int] = []
    session_summaries: list[dict[str, Any]] = []
    feedback_by_session: dict[str, dict[str, Any]] = {}

    for s in sessions:
        if s.degraded_mode:
            degraded_count += 1
        for b in s.blocking_issues:
            blocker_counter[b] += 1
        for w in s.warnings:
            warning_counter[w] += 1
        if s.disposition:
            disposition_counts[s.disposition] += 1
        session_summaries.append({
            "session_id": s.session_id,
            "timestamp_start": s.timestamp_start,
            "degraded_mode": s.degraded_mode,
            "blocking_count": len(s.blocking_issues),
            "warnings_count": len(s.warnings),
            "disposition": s.disposition,
        })
        fb = load_feedback(s.session_id, pilot_dir)
        if fb:
            feedback_by_session[s.session_id] = fb.to_dict()
            if fb.operator_friction_notes:
                operator_friction.append(fb.operator_friction_notes.strip())
            if fb.user_quote:
                user_quotes.append(fb.user_quote.strip())
            if fb.usefulness_score:
                usefulness_scores.append(fb.usefulness_score)

    structured_user_quote_count = 0
    structured_friction_count = 0
    concern_next_steps = 0
    concern_report_location = 0
    for fb_dict in feedback_by_session.values():
        if (fb_dict.get("user_quote") or "").strip():
            structured_user_quote_count += 1
        if (fb_dict.get("operator_friction_notes") or "").strip():
            structured_friction_count += 1
        text = " ".join(
            str(fb_dict.get(k, "")) for k in ("freeform_notes", "operator_friction_notes")
        ).lower()
        if "next step" in text or "specific" in text or "next steps" in text:
            concern_next_steps += 1
        if "report location" in text or "output location" in text or "where to find" in text or "clearer report" in text:
            concern_report_location += 1

    grounded_notes_count = 0
    ungrounded_notes_count = 0
    for s in sessions:
        notes = (s.operator_notes or "").lower()
        if "ungrounded" in notes or "no retrieval" in notes or "generic" in notes:
            ungrounded_notes_count += 1
        elif "grounded" in notes:
            grounded_notes_count += 1

    recurring_blockers = [
        b for b, c in blocker_counter.most_common(20) if c >= 1]
    warning_freq = dict(warning_counter.most_common(20))
    avg_usefulness = sum(usefulness_scores) / \
        len(usefulness_scores) if usefulness_scores else 0

    recommendation = []
    if recurring_blockers:
        recommendation.append(
            "Address recurring blockers before next pilot batch.")
    if degraded_count > len(sessions) // 2 and len(sessions) >= 2:
        recommendation.append(
            "Degraded mode frequent; consider training adapter or documenting baseline-only as expected.")
    if disposition_counts.get("pause", 0) > 0:
        recommendation.append(
            "At least one session disposition was 'pause'; review before continuing.")
    if usefulness_scores and avg_usefulness >= 3:
        recommendation.append(
            "Usefulness scores support continuing pilot with current scope.")
    if not recommendation:
        recommendation.append(
            "Review session notes and feedback; no automatic recommendation.")

    concern_patterns: dict[str, int] = {}
    if concern_next_steps:
        concern_patterns["next_steps_specificity"] = concern_next_steps
    if concern_report_location:
        concern_patterns["report_location_clarity"] = concern_report_location

    evidence_quality = {
        "structured_user_quote_count": structured_user_quote_count,
        "structured_friction_count": structured_friction_count,
        "concern_next_steps_specificity": concern_next_steps,
        "concern_report_location_clarity": concern_report_location,
        "grounded_notes_count": grounded_notes_count,
        "ungrounded_notes_count": ungrounded_notes_count,
    }

    return {
        "sessions_count": len(sessions),
        "recurring_blockers": recurring_blockers,
        "blocker_counts": dict(blocker_counter),
        "warning_counts": warning_freq,
        "degraded_count": degraded_count,
        "degraded_pct": round(100.0 * degraded_count / len(sessions), 1) if sessions else 0,
        "disposition_counts": dict(disposition_counts),
        "operator_friction_notes": operator_friction[:30],
        "user_quotes": user_quotes[:20],
        "avg_usefulness": round(avg_usefulness, 2),
        "recommendation_summary": recommendation,
        "session_summaries": session_summaries,
        "feedback_by_session": feedback_by_session,
        "concern_patterns": concern_patterns,
        "evidence_quality": evidence_quality,
    }


def write_aggregate_report(
    pilot_dir: Path | str | None = None,
    session_limit: int = 100,
) -> tuple[Path, Path]:
    """Write aggregate_report.json and aggregate_report.md. Returns (json_path, md_path)."""
    root = _pilot_root(pilot_dir)
    root.mkdir(parents=True, exist_ok=True)
    data = aggregate_sessions(pilot_dir, session_limit=session_limit)

    json_path = root / AGGREGATE_JSON
    json_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    lines = [
        "# Pilot aggregate report",
        "",
        f"**Sessions included:** {data['sessions_count']}",
        f"**Degraded mode:** {data['degraded_count']} sessions ({data['degraded_pct']}%)",
        "",
    ]
    if data["sessions_count"] == 0:
        lines.append(
            "No pilot sessions found. Run `pilot start-session`, complete at least one session, then re-run `pilot aggregate`.")
        lines.append("")
    eq = data.get("evidence_quality", {})
    if data["sessions_count"] > 0:
        lines.extend([
            "## Structured evidence summary",
            "",
            "Counts below use **structured fields only** (from `--user-quote` and `--friction`). Freeform notes are not parsed as quotes or friction.",
            "",
            f"- Feedback entries with structured user quote: {eq.get('structured_user_quote_count', 0)}",
            f"- Feedback entries with structured friction: {eq.get('structured_friction_count', 0)}",
            f"- Sessions with next-steps/specificity concern (from notes or friction text): {eq.get('concern_next_steps_specificity', 0)}",
            f"- Sessions with report/output-location clarity concern: {eq.get('concern_report_location_clarity', 0)}",
            f"- Sessions noted as grounded (operator notes): {eq.get('grounded_notes_count', 0)}",
            f"- Sessions noted as ungrounded: {eq.get('ungrounded_notes_count', 0)}",
            "",
        ])
    lines.extend([
        "## Recurring blockers",
        "",
    ])
    for b in data.get("recurring_blockers", []):
        count = data.get("blocker_counts", {}).get(b, 0)
        lines.append(f"- {b} (×{count})")
    if not data.get("recurring_blockers"):
        lines.append("- (none)")
    lines.extend([
        "",
        "## Warning frequency",
        "",
    ])
    for w, c in list(data.get("warning_counts", {}).items())[:15]:
        lines.append(f"- {w}: {c}")
    if not data.get("warning_counts"):
        lines.append("- (none)")
    lines.extend([
        "",
        "## Disposition counts",
        "",
    ])
    for d, c in data.get("disposition_counts", {}).items():
        lines.append(f"- {d}: {c}")
    if not data.get("disposition_counts"):
        lines.append("- (none)")
    lines.extend([
        "",
        "## Recommendation",
        "",
    ])
    for r in data.get("recommendation_summary", []):
        lines.append(f"- {r}")
    concern = data.get("concern_patterns", {})
    if concern:
        lines.extend([
            "",
            "## Evidence quality / concern patterns",
            "",
        ])
        if concern.get("next_steps_specificity"):
            lines.append(
                f"- Feedback mentioning next steps / specificity: {concern['next_steps_specificity']} session(s)")
        if concern.get("report_location_clarity"):
            lines.append(
                f"- Feedback mentioning report/output location clarity: {concern['report_location_clarity']} session(s)")
        lines.append("")
    lines.extend([
        "",
        "## Operator friction (excerpts)",
        "",
        "*From structured `--friction` field only.*",
        "",
    ])
    for n in data.get("operator_friction_notes", [])[:10]:
        lines.append(f"- {n[:200]}")
    if not data.get("operator_friction_notes"):
        lines.append("- (none)")
    lines.extend([
        "",
        "## User quotes (excerpts)",
        "",
        "*From structured `--user-quote` field only.*",
        "",
    ])
    for q in data.get("user_quotes", [])[:5]:
        lines.append(f"- \"{q[:150]}\"")
    if not data.get("user_quotes"):
        lines.append("- (none)")
    lines.append("")

    md_path = root / AGGREGATE_MD
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path, md_path

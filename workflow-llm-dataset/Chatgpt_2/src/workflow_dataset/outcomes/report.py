"""
M24N–M24Q: Outcome report formatting — session, patterns, recommend-improvements.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.outcomes.models import SessionOutcome
from workflow_dataset.outcomes.store import get_session_outcome, list_session_outcomes
from workflow_dataset.outcomes.patterns import repeated_block_patterns, repeated_success_patterns, most_useful_per_pack
from workflow_dataset.outcomes.signals import generate_improvement_signals
from workflow_dataset.outcomes.bridge import next_run_recommendations, pack_refinement_suggestions, outcome_to_correction_suggestions
from workflow_dataset.outcomes.scorecard import build_pack_scorecard, build_improvement_backlog


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def format_session_outcome(
    outcome: SessionOutcome | None,
    session_id: str | None = None,
    repo_root: Path | str | None = None,
) -> str:
    """Format a single session outcome for console output."""
    if outcome is None and session_id:
        outcome = get_session_outcome(session_id, repo_root)
    if outcome is None:
        return "No session outcome found."
    lines = [
        f"Session: {outcome.session_id}",
        f"  pack_id: {outcome.pack_id or '—'}  disposition: {outcome.disposition or '—'}",
        f"  start: {outcome.timestamp_start or '—'}  end: {outcome.timestamp_end or '—'}",
        f"  tasks: {len(outcome.task_outcomes)}  blocked: {len(outcome.blocked_causes)}  useful: {len(outcome.usefulness_confirmations)}",
    ]
    if outcome.summary_text:
        lines.append("  summary: " + (outcome.summary_text[:200] + "…" if len(outcome.summary_text) > 200 else outcome.summary_text))
    for b in outcome.blocked_causes[:5]:
        lines.append(f"  block: {b.cause_code}  ref={b.source_ref or '—'}")
    for u in outcome.usefulness_confirmations[:5]:
        lines.append(f"  useful: {u.source_ref or '—'}  score={u.usefulness_score}  confirmed={u.operator_confirmed}")
    return "\n".join(lines)


def format_patterns(repo_root: Path | str | None = None) -> str:
    """Format repeated block/success patterns and most useful per pack."""
    root = _repo_root(repo_root)
    lines = ["=== Outcome patterns ===", ""]
    blocks = repeated_block_patterns(repo_root=root, min_occurrences=2, limit=15)
    lines.append("[Repeated blocks]")
    if not blocks:
        lines.append("  (none)")
    else:
        for b in blocks:
            lines.append(f"  {b['cause_code']}  ref={b['source_ref']}  count={b['count']}  sessions={b.get('sample_session_ids', [])[:3]}")
    lines.append("")
    success = repeated_success_patterns(repo_root=root, min_occurrences=2, limit=15)
    lines.append("[Repeated success]")
    if not success:
        lines.append("  (none)")
    else:
        for s in success:
            lines.append(f"  ref={s['source_ref']}  pack={s['pack_id']}  count={s['count']}")
    lines.append("")
    useful = most_useful_per_pack(repo_root=root, top_n=5)
    lines.append("[Most useful per pack]")
    if not useful:
        lines.append("  (none)")
    else:
        for u in useful[:20]:
            lines.append(f"  pack={u['pack_id']}  ref={u['source_ref']}  score={u['score']}")
    return "\n".join(lines)


def format_recommend_improvements(repo_root: Path | str | None = None) -> str:
    """Format improvement signals and bridge recommendations."""
    root = _repo_root(repo_root)
    signals = generate_improvement_signals(repo_root=root)
    lines = ["=== Improvement signals ===", ""]
    for s in signals.get("signals_list", [])[:20]:
        lines.append(f"  [{s.get('priority', '')}] {s.get('signal_type', '')}: {s.get('title', '')}")
        if s.get("detail"):
            lines.append(f"    {s['detail']}")
    lines.append("")
    lines.append("--- Next-run recommendations ---")
    recs = next_run_recommendations(repo_root=root)
    if not recs:
        lines.append("  (none)")
    else:
        for r in recs[:10]:
            lines.append(f"  {r.get('kind', '')}: {r.get('title', '')}")
            if r.get("detail"):
                lines.append(f"    {r['detail']}")
    lines.append("")
    lines.append("--- Pack refinement suggestions ---")
    pack_recs = pack_refinement_suggestions(repo_root=root)
    if not pack_recs:
        lines.append("  (none)")
    else:
        for p in pack_recs[:10]:
            lines.append(f"  {p.get('kind', '')}: {p.get('source_ref', '')}  {p.get('detail', '')}")
    lines.append("")
    lines.append("--- Correction suggestions (advisory) ---")
    corr = outcome_to_correction_suggestions(repo_root=root, limit=5)
    if not corr:
        lines.append("  (none)")
    else:
        for c in corr:
            lines.append(f"  {c.get('suggested_category', '')}  ref={c.get('source_ref', '')}  {c.get('reason', '')}")
    return "\n".join(lines)


def format_pack_scorecard(
    scorecard: dict[str, Any] | None = None,
    pack_id: str | None = None,
    repo_root: Path | str | None = None,
) -> str:
    """Format pack scorecard for console. Operator-readable."""
    if scorecard is None and pack_id:
        scorecard = build_pack_scorecard(pack_id, repo_root)
    if not scorecard:
        return "No scorecard (provide pack_id or scorecard dict)."
    lines = [
        f"=== Pack scorecard: {scorecard.get('pack_id', '')} ===",
        "",
        "[Usefulness]",
        "  " + (scorecard.get("usefulness") or {}).get("summary", "—"),
    ]
    for ref in (scorecard.get("usefulness") or {}).get("high_value_refs", [])[:5]:
        lines.append(f"    high_value: {ref}")
    lines.extend(["", "[Blockers]", "  " + (scorecard.get("blockers") or {}).get("summary", "—")])
    for d in (scorecard.get("blockers") or {}).get("recurring_detail", [])[:5]:
        lines.append(f"    {d.get('cause_code', '')}  ref={d.get('source_ref', '')}  count={d.get('count', 0)}")
    lines.extend(["", "[Readiness]", "  " + (scorecard.get("readiness") or {}).get("summary", "—")])
    lines.extend(["", "[Trusted-real suitability]", "  " + (scorecard.get("trusted_real_suitability") or {}).get("summary", "—")])
    lines.extend(["", "[Session reuse strength]", "  " + (scorecard.get("session_reuse_strength") or {}).get("summary", "—")])
    lines.append("")
    backlog = scorecard.get("improvement_backlog") or []
    lines.append(f"[Improvement backlog]  {len(backlog)} items")
    for i, item in enumerate(backlog[:15], 1):
        lines.append(f"  {i}. [{item.get('priority', '')}] {item.get('kind', '')}: {item.get('title', '')[:60]}")
        if item.get("detail"):
            lines.append(f"      {item['detail'][:70]}")
    return "\n".join(lines)


def format_improvement_backlog(
    repo_root: Path | str | None = None,
    pack_id: str | None = None,
) -> str:
    """Format improvement backlog for console. Operator-readable."""
    root = _repo_root(repo_root)
    items = build_improvement_backlog(repo_root=root, pack_id=pack_id)
    lines = ["=== Improvement backlog ==="]
    if pack_id:
        lines.append(f"  pack_id filter: {pack_id}")
    lines.append("")
    if not items:
        lines.append("  (none)")
    else:
        for i, item in enumerate(items[:25], 1):
            pack = item.get("pack_id", "") or "(global)"
            lines.append(f"  {i}. [{item.get('priority', '')}] {item.get('kind', '')}  pack={pack}")
            lines.append(f"      {item.get('title', '')[:70]}")
            if item.get("detail"):
                lines.append(f"      {item['detail'][:70]}")
    return "\n".join(lines)

"""
M23V / M23O: Format daily inbox digest as text report. What changed, inbox items (why now), top next.
"""

from __future__ import annotations

from workflow_dataset.daily.inbox import DailyDigest, build_daily_digest


def format_inbox_report(
    digest: DailyDigest | None = None,
    repo_root=None,
    include_explain: bool = False,
) -> str:
    """Produce human-readable daily inbox report. If digest is None, builds from repo_root. M23O: what changed, inbox items with reason/trust/mode/blockers/outcome."""
    if digest is None:
        digest = build_daily_digest(repo_root)
    lines: list[str] = []
    lines.append("=== Daily Inbox (start here) ===")
    if getattr(digest, "created_at", ""):
        lines.append(f"  {digest.created_at}")
    lines.append("")

    if digest.errors:
        lines.append("[Errors] " + "; ".join(digest.errors[:5]))
        lines.append("")

    if getattr(digest, "what_changed", None) and digest.what_changed:
        lines.append("[What changed since last snapshot]")
        for s in digest.what_changed[:10]:
            lines.append(f"  {s}")
        lines.append("")

    lines.append("[Relevant work]")
    lines.append("  Jobs: " + (", ".join(digest.relevant_job_ids[:10]) or "—"))
    lines.append("  Routines: " + (", ".join(digest.relevant_routine_ids[:5]) or "—"))
    lines.append("")

    if getattr(digest, "inbox_items", None) and digest.inbox_items:
        lines.append("[Inbox items — reason, trust, mode, blockers, expected outcome]")
        for item in digest.inbox_items[:15]:
            iid = item.get("id", "")
            kind = item.get("kind", "")
            reason = item.get("reason", "")
            trust = item.get("trust_level", "")
            mode = item.get("mode_available", "")
            blockers = item.get("blockers") or []
            outcome = item.get("expected_outcome", "")
            lines.append(f"  {kind} {iid}")
            lines.append(f"    reason: {reason}  trust: {trust}  mode: {mode}")
            if blockers:
                lines.append(f"    blockers: {'; '.join(str(b) for b in blockers[:3])}")
            lines.append(f"    expected_outcome: {outcome[:80]}{'…' if len(outcome) > 80 else ''}")
        lines.append("")

    if digest.blocked_items:
        lines.append("[Blocked]")
        for b in digest.blocked_items[:10]:
            lines.append(f"  {b.get('kind', '')} {b.get('id', '')}: {b.get('reason', '')}")
        lines.append("")

    if digest.reminders_due:
        lines.append("[Reminders due]")
        for r in digest.reminders_due[:10]:
            title = r.get("title") or r.get("routine_id") or r.get("reminder_id", "")
            lines.append(f"  {title}")
        lines.append("")

    if digest.approvals_needing_refresh:
        lines.append("[Approvals needing refresh]")
        lines.append("  " + ", ".join(digest.approvals_needing_refresh[:10]))
        lines.append("")

    if digest.trust_regressions:
        lines.append("[Trust regressions]")
        for t in digest.trust_regressions:
            lines.append(f"  {t}")
        lines.append("")

    if digest.recent_successful_runs:
        lines.append("[Recent successful runs]")
        for r in digest.recent_successful_runs[:5]:
            pid = r.get("plan_run_id") or r.get("job_pack_id") or "—"
            lines.append(f"  {pid}  {r.get('mode', '')}  {r.get('timestamp', '')}")
        lines.append("")

    if digest.corrections_review_recommended or digest.unresolved_corrections_count:
        lines.append("[Corrections]")
        lines.append(f"  Unresolved / review: {digest.unresolved_corrections_count}")
        if digest.corrections_review_recommended:
            lines.append("  Review recommended: " + ", ".join(digest.corrections_review_recommended[:5]))
        lines.append("")

    lines.append("--- Top next recommended action ---")
    top = getattr(digest, "top_next_recommended", None) or {}
    if top:
        lines.append(f"  label: {top.get('label', '')}")
        lines.append(f"  reason: {top.get('reason', '')}")
        lines.append(f"  command: {top.get('command', '')}")
    lines.append("--- Recommended next action ---")
    lines.append(f"  {digest.recommended_next_action}")
    lines.append(f"  {digest.recommended_next_detail}")
    lines.append("")
    if digest.domain_pack_suggestions:
        lines.append("[Domain-pack suggestions]")
        for s in digest.domain_pack_suggestions[:5]:
            lines.append(f"  {s}")
        lines.append("")
    lines.append("(Operator-controlled. No automatic changes.)")
    return "\n".join(lines)


def format_explain_why_now(digest: DailyDigest | None = None, repo_root=None) -> str:
    """Explain why each inbox item is shown now: reason, trust level, mode available, blockers, expected outcome. M23O."""
    if digest is None:
        digest = build_daily_digest(repo_root)
    lines: list[str] = []
    lines.append("=== Inbox: why these items now ===")
    lines.append("")
    if not getattr(digest, "inbox_items", None) or not digest.inbox_items:
        lines.append("No inbox items. Run 'workflow-dataset copilot recommend' or 'workflow-dataset jobs seed'.")
        return "\n".join(lines)
    for item in digest.inbox_items:
        lines.append(f"  [{item.get('kind', '')}] {item.get('id', '')}")
        lines.append(f"    reason: {item.get('reason', '')}")
        lines.append(f"    trust_level: {item.get('trust_level', '')}")
        lines.append(f"    mode_available: {item.get('mode_available', '')}")
        blockers = item.get("blockers") or []
        lines.append(f"    blockers: {blockers if blockers else 'none'}")
        lines.append(f"    expected_outcome: {item.get('expected_outcome', '')}")
        lines.append("")
    top = getattr(digest, "top_next_recommended", None) or {}
    if top:
        lines.append("--- Top next ---")
        lines.append(f"  {top.get('label', '')}: {top.get('reason', '')}")
        lines.append(f"  command: {top.get('command', '')}")
    return "\n".join(lines)

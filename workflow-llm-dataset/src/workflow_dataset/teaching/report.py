"""
M26I–M26L: Skill library report — draft/accepted/rejected, pack-associated, needing review, weak/unclear.
"""

from __future__ import annotations

from typing import Any

from workflow_dataset.teaching.skill_store import list_skills


def build_skill_report(repo_root=None) -> dict[str, Any]:
    """Aggregate counts and lists for skills: draft, accepted, rejected, pack-linked, needing review, weak/unclear."""
    drafts = list_skills(status="draft", repo_root=repo_root, limit=500)
    accepted = list_skills(status="accepted", repo_root=repo_root, limit=500)
    rejected = list_skills(status="rejected", repo_root=repo_root, limit=200)
    all_skills = drafts + accepted + rejected
    pack_linked = [s for s in all_skills if s.pack_associations]
    needing_review = drafts  # all drafts need review
    weak_unclear = [
        s for s in all_skills
        if s.trust_readiness_status in ("blocked", "unclear") or not s.normalized_steps
    ]
    return {
        "draft_count": len(drafts),
        "accepted_count": len(accepted),
        "rejected_count": len(rejected),
        "draft_ids": [s.skill_id for s in drafts[:30]],
        "accepted_ids": [s.skill_id for s in accepted[:30]],
        "rejected_ids": [s.skill_id for s in rejected[:20]],
        "pack_linked_count": len(pack_linked),
        "pack_linked_ids": [s.skill_id for s in pack_linked[:30]],
        "needing_review_count": len(needing_review),
        "needing_review_ids": [s.skill_id for s in needing_review[:30]],
        "weak_unclear_count": len(weak_unclear),
        "weak_unclear_ids": [s.skill_id for s in weak_unclear[:20]],
        "recent_accepted": [s.skill_id for s in accepted[:10]],
    }


def format_skill_report(report: dict[str, Any] | None = None, repo_root=None) -> str:
    """Produce a console report. If report is None, builds from repo."""
    if report is None:
        report = build_skill_report(repo_root)
    lines = [
        "=== Teaching / Skill library ===",
        "",
        f"  draft: {report.get('draft_count', 0)}  accepted: {report.get('accepted_count', 0)}  rejected: {report.get('rejected_count', 0)}",
        f"  pack-linked: {report.get('pack_linked_count', 0)}  needing_review: {report.get('needing_review_count', 0)}  weak/unclear: {report.get('weak_unclear_count', 0)}",
        "",
    ]
    if report.get("draft_ids"):
        lines.append("  draft_ids (sample): " + ", ".join(report["draft_ids"][:10]))
    if report.get("recent_accepted"):
        lines.append("  recent_accepted: " + ", ".join(report["recent_accepted"][:5]))
    if report.get("pack_linked_ids"):
        lines.append("  pack_linked (sample): " + ", ".join(report["pack_linked_ids"][:5]))
    lines.append("")
    return "\n".join(lines)

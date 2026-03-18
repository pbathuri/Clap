"""
M26L.1: Skill scorecards + pack/goal coverage. Operator-readable.
"""

from __future__ import annotations

from typing import Any

from workflow_dataset.teaching.skill_store import list_skills


def _all_skills(repo_root=None, limit: int = 1000):
    drafts = list_skills(status="draft", repo_root=repo_root, limit=limit)
    accepted = list_skills(status="accepted", repo_root=repo_root, limit=limit)
    rejected = list_skills(status="rejected", repo_root=repo_root, limit=limit)
    seen = set()
    out = []
    for s in drafts + accepted + rejected:
        if s.skill_id not in seen:
            seen.add(s.skill_id)
            out.append(s)
    return out


def build_skill_scorecard(repo_root=None) -> dict[str, Any]:
    """
    First-draft skill scorecard: draft vs accepted vs trusted counts,
    pack coverage (strong/weak), goal-family coverage, where more demos needed.
    """
    skills = _all_skills(repo_root=repo_root)
    draft = [s for s in skills if s.status == "draft"]
    accepted = [s for s in skills if s.status == "accepted"]
    rejected = [s for s in skills if s.status == "rejected"]
    trusted = [s for s in skills if s.simulate_only_or_trusted_real == "trusted_real_candidate" and s.status == "accepted"]

    # By pack: collect every pack_id from pack_associations
    by_pack: dict[str, dict[str, Any]] = {}
    for s in skills:
        for pack_id in (s.pack_associations or []):
            if not pack_id:
                continue
            if pack_id not in by_pack:
                by_pack[pack_id] = {"draft": 0, "accepted": 0, "trusted_real": 0, "skill_ids": []}
            rec = by_pack[pack_id]
            if s.status == "draft":
                rec["draft"] += 1
            elif s.status == "accepted":
                rec["accepted"] += 1
                if s.simulate_only_or_trusted_real == "trusted_real_candidate":
                    rec["trusted_real"] += 1
            rec["skill_ids"].append(s.skill_id)

    # Strong coverage: pack has >= 2 accepted OR >= 1 trusted_real
    packs_strong = [pid for pid, r in by_pack.items() if r["accepted"] >= 2 or r["trusted_real"] >= 1]
    packs_weak = [pid for pid, r in by_pack.items() if r["accepted"] < 2 and r["trusted_real"] < 1]
    packs_no_skills: list[str] = []  # known packs with 0 skills — we don't have pack registry here, so leave empty or extend later

    # By goal family
    by_goal: dict[str, dict[str, Any]] = {}
    for s in skills:
        gf = (s.goal_family or "").strip() or "(unspecified)"
        if gf not in by_goal:
            by_goal[gf] = {"draft": 0, "accepted": 0, "trusted_real": 0, "skill_ids": []}
        rec = by_goal[gf]
        if s.status == "draft":
            rec["draft"] += 1
        elif s.status == "accepted":
            rec["accepted"] += 1
            if s.simulate_only_or_trusted_real == "trusted_real_candidate":
                rec["trusted_real"] += 1
        rec["skill_ids"].append(s.skill_id)

    # Under-taught: goal family with 0 skills or only 1 skill or no accepted
    under_taught_goals = [
        gf for gf, r in by_goal.items()
        if r["accepted"] == 0 or (r["draft"] + r["accepted"]) <= 1
    ]
    # Where more demonstrations are needed: under-taught goal families + packs with no/weak coverage
    more_demos_goals = [gf for gf, r in by_goal.items() if (r["draft"] + r["accepted"]) == 0]
    more_demos_packs = [pid for pid in packs_weak if by_pack[pid]["accepted"] == 0 and by_pack[pid]["draft"] == 0]

    return {
        "summary": {
            "draft_count": len(draft),
            "accepted_count": len(accepted),
            "rejected_count": len(rejected),
            "trusted_real_count": len(trusted),
        },
        "by_pack": by_pack,
        "packs_strong_coverage": packs_strong,
        "packs_weak_coverage": packs_weak,
        "by_goal_family": by_goal,
        "under_taught_goal_families": under_taught_goals,
        "more_demos_needed_goal_families": more_demos_goals,
        "more_demos_needed_packs": more_demos_packs,
    }


def format_skill_scorecard(scorecard: dict[str, Any] | None = None, repo_root=None) -> str:
    """Produce operator-readable skill scorecard."""
    if scorecard is None:
        scorecard = build_skill_scorecard(repo_root)
    lines = [
        "=== Skill scorecard ===",
        "",
    ]
    summary = scorecard.get("summary", {})
    lines.append("  [Summary] draft=%s  accepted=%s  rejected=%s  trusted_real=%s" % (
        summary.get("draft_count", 0),
        summary.get("accepted_count", 0),
        summary.get("rejected_count", 0),
        summary.get("trusted_real_count", 0),
    ))
    lines.append("")
    strong = scorecard.get("packs_strong_coverage", [])
    weak = scorecard.get("packs_weak_coverage", [])
    lines.append("  [Pack coverage] strong=%s  weak=%s" % (len(strong), len(weak)))
    if strong:
        lines.append("    strong: " + ", ".join(strong[:15]))
    if weak:
        lines.append("    weak: " + ", ".join(weak[:15]))
    lines.append("")
    under = scorecard.get("under_taught_goal_families", [])
    lines.append("  [Goal families under-taught] %s" % len(under))
    if under:
        lines.append("    " + ", ".join(under[:15]))
    lines.append("")
    more_goals = scorecard.get("more_demos_needed_goal_families", [])
    more_packs = scorecard.get("more_demos_needed_packs", [])
    lines.append("  [More demonstrations needed]")
    lines.append("    goal_families (none yet): " + (", ".join(more_goals[:10]) if more_goals else "—"))
    lines.append("    packs (none linked yet): " + (", ".join(more_packs[:10]) if more_packs else "—"))
    lines.append("")
    return "\n".join(lines)


def build_pack_goal_coverage_report(repo_root=None) -> dict[str, Any]:
    """Per-pack and per-goal coverage for drill-down."""
    scorecard = build_skill_scorecard(repo_root=repo_root)
    by_pack = scorecard.get("by_pack", {})
    by_goal = scorecard.get("by_goal_family", {})
    pack_rows = []
    for pack_id, r in sorted(by_pack.items()):
        pack_rows.append({
            "pack_id": pack_id,
            "draft": r["draft"],
            "accepted": r["accepted"],
            "trusted_real": r["trusted_real"],
            "coverage": "strong" if (r["accepted"] >= 2 or r["trusted_real"] >= 1) else "weak",
        })
    goal_rows = []
    for gf, r in sorted(by_goal.items()):
        goal_rows.append({
            "goal_family": gf,
            "draft": r["draft"],
            "accepted": r["accepted"],
            "trusted_real": r["trusted_real"],
            "under_taught": r["accepted"] == 0 or (r["draft"] + r["accepted"]) <= 1,
        })
    return {
        "packs": pack_rows,
        "goal_families": goal_rows,
        "summary": scorecard.get("summary", {}),
    }


def format_pack_goal_coverage_report(report: dict[str, Any] | None = None, repo_root=None) -> str:
    """Operator-readable pack and goal family coverage."""
    if report is None:
        report = build_pack_goal_coverage_report(repo_root)
    lines = [
        "=== Pack / Goal skill coverage ===",
        "",
    ]
    summary = report.get("summary", {})
    lines.append("  Summary: draft=%s  accepted=%s  trusted_real=%s" % (
        summary.get("draft_count", 0),
        summary.get("accepted_count", 0),
        summary.get("trusted_real_count", 0),
    ))
    lines.append("")
    lines.append("  [By pack]")
    for row in report.get("packs", [])[:30]:
        lines.append("    %s  draft=%s  accepted=%s  trusted_real=%s  coverage=%s" % (
            row["pack_id"], row["draft"], row["accepted"], row["trusted_real"], row["coverage"]))
    lines.append("")
    lines.append("  [By goal family]")
    for row in report.get("goal_families", [])[:30]:
        ut = " under_taught" if row["under_taught"] else ""
        lines.append("    %s  draft=%s  accepted=%s  trusted_real=%s%s" % (
            row["goal_family"], row["draft"], row["accepted"], row["trusted_real"], ut))
    lines.append("")
    return "\n".join(lines)

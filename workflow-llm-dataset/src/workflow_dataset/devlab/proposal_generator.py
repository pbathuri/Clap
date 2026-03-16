"""
M21W-F3: Generate devlab proposal from repo intake + model compare. Advisory only; no code modification.
Outputs: devlab_proposal.md, cursor_prompt.txt, rfc_skeleton.md, ranked next-patch recommendation.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from workflow_dataset.devlab.config import get_model_compare_dir, get_proposals_dir, get_reports_dir


def load_intake_reports(root: Path | str | None = None) -> list[dict[str, Any]]:
    """Load all repo intake reports from reports dir. Each dict has repo_id, _path, and report fields."""
    reports_dir = get_reports_dir(root)
    out: list[dict[str, Any]] = []
    for p in reports_dir.glob("repo_intake_report_*.json"):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            data["_path"] = str(p)
            out.append(data)
        except Exception:
            pass
    return out


def load_model_compare_report(root: Path | str | None = None) -> dict[str, Any] | None:
    """Load model_compare_report.json if present."""
    compare_dir = get_model_compare_dir(root)
    path = compare_dir / "model_compare_report.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _recommendation_from_reports(
    reports: list[dict[str, Any]],
    mc: dict[str, Any] | None,
) -> dict[str, Any]:
    """Build recommendation: why it matters, product value, complexity, build next, avoid."""
    out: dict[str, Any] = {
        "why_matters": "",
        "product_value": "",
        "engineering_complexity": "",
        "build_next": [],
        "avoid": [],
    }
    if not reports and not mc:
        out["why_matters"] = "No intake or model comparison data yet. Run devlab ingest-repo, repo-report, and compare-models to seed proposals."
        return out
    if reports:
        best = max(reports, key=lambda r: float(r.get("composite_score") or 0))
        rec = best.get("d2_recommendation") or "inspect_further"
        out["why_matters"] = (
            f"Repo intake suggests at least one candidate ({best.get('repo_id')}) with recommendation '{rec}' "
            "and composite score {:.2f}. Model comparison informs which provider/workflow to target.".format(
                float(best.get("composite_score") or 0)
            )
        )
        out["product_value"] = (
            "Adopting patterns or a prototype from scored repos can reduce time-to-value for workflow/UI/eval capabilities."
        )
        scores = best.get("usefulness_scores") or {}
        comp = float(scores.get("implementation_complexity") or 0.5)
        if comp > 0.6:
            out["engineering_complexity"] = "Medium–high: structure and dependencies suggest non-trivial integration."
        elif comp < 0.4:
            out["engineering_complexity"] = "Low: small surface area and clear docs."
        else:
            out["engineering_complexity"] = "Medium: standard integration effort."
        for r in reports:
            rec_r = r.get("d2_recommendation") or ""
            if rec_r == "prototype_candidate":
                out["build_next"].append(f"Prototype from {r.get('repo_id')} (score {r.get('composite_score', 0):.2f})")
            elif rec_r == "inspect_further":
                out["build_next"].append(f"Inspect {r.get('repo_id')} for patterns or API shape")
            elif rec_r == "do_not_use":
                out["avoid"].append(f"Do not reuse {r.get('repo_id')} as-is (risk or fit)")
        if not out["build_next"]:
            out["build_next"].append("Run more intake and score-repos to get prototype_candidate or inspect_further entries.")
        if not out["avoid"]:
            out["avoid"].append("Avoid applying unreviewed external code; use advisory only.")
    if mc:
        out["why_matters"] = (out["why_matters"] or "") + " Model comparison provides workflow/provider baseline."
    return out


def _ranked_next_patch(reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Rank repos as next likely patch: by composite_score desc, then d2_recommendation priority."""
    priority = {"prototype_candidate": 3, "inspect_further": 2, "borrow_pattern_only": 1, "do_not_use": 0}
    decorated = [
        (float(r.get("composite_score") or 0), priority.get(r.get("d2_recommendation") or "", 0), r)
        for r in reports
    ]
    decorated.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return [
        {
            "rank": i + 1,
            "repo_id": r.get("repo_id"),
            "composite_score": r.get("composite_score"),
            "d2_recommendation": r.get("d2_recommendation"),
        }
        for i, (_, _, r) in enumerate(decorated)
    ]


def generate_proposal(
    root: Path | str | None = None,
    repo_id: str | None = None,
) -> dict[str, Any]:
    """
    Generate proposal: devlab_proposal.md, cursor_prompt.txt, rfc_skeleton.md, manifest.json.
    If repo_id is set, filter intake to that repo only. Advisory only.
    Returns proposal_id, proposal_path, intake_count, model_compare_present, devlab_proposal_md, cursor_prompt_txt,
    next_patch_ranked, recommendation.
    """
    root = Path(root) if root else None
    proposals_dir = get_proposals_dir(root)
    reports = load_intake_reports(root)
    if repo_id:
        reports = [r for r in reports if (r.get("repo_id") or "") == repo_id]
    mc = load_model_compare_report(root)
    recommendation = _recommendation_from_reports(reports, mc)
    next_patch_ranked = _ranked_next_patch(reports)

    proposal_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    prop_dir = proposals_dir / proposal_id
    prop_dir.mkdir(parents=True, exist_ok=True)

    # ---- devlab_proposal.md ----
    md_lines = [
        "# Devlab proposal (advisory)",
        "",
        "This is an **advisory** proposal. No code modification is applied. All outputs are local and reviewable.",
        "",
        "## Why this proposal matters",
        "",
        recommendation.get("why_matters") or "No intake or model comparison data yet.",
        "",
        "## Expected product value",
        "",
        recommendation.get("product_value") or "Review repo intake and model compare to identify value.",
        "",
        "## Expected engineering complexity",
        "",
        recommendation.get("engineering_complexity") or "Assess from repo intake scores and dependency heaviness.",
        "",
        "## What to build next",
        "",
    ]
    for item in recommendation.get("build_next") or []:
        md_lines.append(f"- {item}")
    md_lines.extend(["", "## What not to do", ""])
    for item in recommendation.get("avoid") or []:
        md_lines.append(f"- {item}")
    md_lines.extend(["", "## Ranked next likely patch", ""])
    if next_patch_ranked:
        md_lines.append("| Rank | Repo | Score | Recommendation |")
        md_lines.append("|------|------|-------|----------------|")
        for row in next_patch_ranked:
            md_lines.append(f"| {row.get('rank')} | {row.get('repo_id')} | {row.get('composite_score')} | {row.get('d2_recommendation')} |")
    else:
        md_lines.append("No ranked repos. Run devlab repo-report and score-repos.")
    md_lines.append("")
    md_lines.append("## Repo intake summary")
    md_lines.append("")
    if not reports:
        md_lines.append("No repo intake reports found.")
    else:
        for r in reports:
            md_lines.append(f"- **{r.get('repo_id')}**: {r.get('summary', '')[:150]}...")
            md_lines.append(f"  - Recommendation: {r.get('d2_recommendation')}  Score: {r.get('composite_score')}")
    md_lines.append("")
    md_lines.append("## Model comparison")
    md_lines.append("")
    if not mc:
        md_lines.append("No model comparison report found.")
    else:
        md_lines.append(f"Workflow: {mc.get('workflow')}")
        for res in mc.get("results") or []:
            md_lines.append(f"- {res.get('provider')}: {res.get('model')} — {str(res.get('output', ''))[:80]}")
    (prop_dir / "devlab_proposal.md").write_text("\n".join(md_lines), encoding="utf-8")

    # ---- cursor_prompt.txt (Cursor-ready) ----
    cursor_lines = [
        "# Cursor prompt — Devlab proposal",
        "",
        "Use this proposal as context. Do not apply code changes without explicit operator approval.",
        "",
        "## Context",
        "",
        "Repo intake: " + (", ".join(r.get("repo_id", "") for r in reports) if reports else "none"),
        "Model comparison: " + (str(mc.get("workflow")) if mc else "none"),
        "",
        "## Suggested next steps",
        "",
    ]
    for item in recommendation.get("build_next") or []:
        cursor_lines.append(f"- {item}")
    cursor_lines.append("")
    cursor_lines.append("## Artifacts (local paths)")
    cursor_lines.append(f"- Proposal: {prop_dir / 'devlab_proposal.md'}")
    cursor_lines.append(f"- RFC skeleton: {prop_dir / 'rfc_skeleton.md'}")
    (prop_dir / "cursor_prompt.txt").write_text("\n".join(cursor_lines), encoding="utf-8")

    # ---- rfc_skeleton.md ----
    rfc_lines = [
        "# RFC: [Title]",
        "",
        "## Context",
        "",
        recommendation.get("why_matters", "")[:500] or "Fill in: what problem or opportunity this addresses.",
        "",
        "## Goals",
        "",
        "- (Primary goal)",
        "- (Success criteria)",
        "",
        "## Non-goals",
        "",
        "- (Out of scope)",
        "",
        "## Proposed approach",
        "",
        "1. (Step one)",
        "2. (Step two)",
        "3. (Integration / testing)",
        "",
        "## Open questions",
        "",
        "- (Unresolved)",
        "",
        "---",
        "*Generated by devlab proposal generator. Advisory only.*",
    ]
    (prop_dir / "rfc_skeleton.md").write_text("\n".join(rfc_lines), encoding="utf-8")

    # ---- manifest.json ----
    manifest = {
        "proposal_id": proposal_id,
        "source": "proposal_generator",
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "intake_count": len(reports),
        "model_compare_present": mc is not None,
        "next_patch_ranked": next_patch_ranked,
        "recommendation": recommendation,
    }
    if repo_id:
        manifest["focused_repo_id"] = repo_id
    (prop_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    return {
        "proposal_id": proposal_id,
        "proposal_path": str(prop_dir),
        "intake_count": len(reports),
        "model_compare_present": mc is not None,
        "devlab_proposal_md": str(prop_dir / "devlab_proposal.md"),
        "cursor_prompt_txt": str(prop_dir / "cursor_prompt.txt"),
        "next_patch_ranked": next_patch_ranked,
        "recommendation": recommendation,
    }


"""
M21W-F2: Ranked shortlist by category (UI, eval, packaging, workflow composition, local model tooling).
Reads intake reports and registry; outputs ranked entries per category.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

CATEGORIES = (
    "UI",
    "eval",
    "packaging",
    "workflow_engine",
    "local_model_tooling",
    "other",
)


def build_shortlist(
    reports_dir: Path | str,
    registry: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """
    Build ranked shortlist by category from intake reports and registry.
    reports_dir: path to dir containing repo_intake_report_<id>.json.
    registry: list of { repo_id, category, url }.
    Returns dict category -> list of { repo_id, composite_score, d2_recommendation, url, ... } sorted by score desc.
    """
    reports_dir = Path(reports_dir)
    by_cat: dict[str, list[dict[str, Any]]] = {c: [] for c in CATEGORIES}
    if "evaluation" not in by_cat:
        by_cat["evaluation"] = []
    cat_by_repo: dict[str, str] = {}
    for e in registry:
        rid = e.get("repo_id") or ""
        cat = (e.get("category") or "other").strip()
        if not cat or cat not in by_cat:
            cat = "other"
        cat_by_repo[rid] = cat

    for p in reports_dir.glob("repo_intake_report_*.json"):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        repo_id = data.get("repo_id", p.stem.replace("repo_intake_report_", ""))
        cat = cat_by_repo.get(repo_id) or data.get("category") or "other"
        if cat not in by_cat:
            by_cat[cat] = []
        score = float(data.get("composite_score") or 0)
        entry = {
            "repo_id": repo_id,
            "composite_score": score,
            "d2_recommendation": data.get("d2_recommendation") or "inspect_further",
            "url": data.get("url") or "",
            "summary": (data.get("summary") or "")[:200],
        }
        if data.get("usefulness_scores"):
            entry["usefulness_scores"] = data["usefulness_scores"]
        if data.get("license_triage"):
            entry["license_triage"] = data["license_triage"]
        by_cat[cat].append(entry)
    for c in by_cat:
        by_cat[c].sort(key=lambda x: x.get("composite_score", 0), reverse=True)
    return by_cat


def write_shortlist_report(
    shortlist: dict[str, list[dict[str, Any]]],
    path: Path | str,
    format: str = "json",
) -> None:
    """Write shortlist to file. format: json or md."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if format.lower() == "md":
        lines = ["# Devlab shortlist by category", ""]
        for cat, entries in shortlist.items():
            if not entries:
                continue
            lines.append(f"## {cat}")
            lines.append("")
            for e in entries:
                lines.append(f"- **{e.get('repo_id')}**  score={e.get('composite_score', 0):.2f}  {e.get('d2_recommendation')}")
                if e.get("url"):
                    lines.append(f"  - {e['url']}")
            lines.append("")
        path.write_text("\n".join(lines), encoding="utf-8")
    else:
        path.write_text(json.dumps(shortlist, indent=2), encoding="utf-8")

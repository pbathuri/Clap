"""
M23M: Corrections impact report. Recent corrections, proposed/applied/reverted, most corrected areas.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from collections import Counter

from workflow_dataset.corrections.store import list_corrections
from workflow_dataset.corrections.propose import propose_updates
from workflow_dataset.corrections.updates import list_proposed_updates, load_update_record
from workflow_dataset.corrections.history import list_applied_updates, list_reverted_updates


def corrections_report(
    repo_root: Path | str | None = None,
    limit_corrections: int = 50,
    limit_updates: int = 20,
) -> dict[str, Any]:
    """Aggregate: recent corrections, proposed updates, applied, reverted, most corrected job/routine ids."""
    root = Path(repo_root).resolve() if repo_root else None
    recent = list_corrections(limit=limit_corrections, repo_root=root)
    proposed = list_proposed_updates(root)
    applied = list_applied_updates(limit=limit_updates, repo_root=root)
    reverted = list_reverted_updates(limit=limit_updates, repo_root=root)

    # Most corrected: by source_reference_id (job or routine)
    by_ref: Counter[str] = Counter()
    for c in recent:
        by_ref[c.source_reference_id or "unknown"] += 1
    most_corrected = [ref for ref, _ in by_ref.most_common(10)]

    return {
        "recent_corrections_count": len(recent),
        "recent_corrections": [c.to_dict() for c in recent[:15]],
        "proposed_updates_count": len(proposed),
        "proposed_updates": [{"update_id": p.update_id, "target_type": p.target_type, "target_id": p.target_id} for p in proposed[:10]],
        "applied_updates_count": len(applied),
        "applied_updates": [u.to_dict() for u in applied[:10]],
        "reverted_updates_count": len(reverted),
        "reverted_updates": [u.to_dict() for u in reverted[:10]],
        "most_corrected_ids": most_corrected,
    }


def format_corrections_report(report: dict[str, Any]) -> str:
    lines = [
        "=== Corrections report (M23M) ===",
        "",
        f"Recent corrections: {report.get('recent_corrections_count', 0)}",
        f"Proposed updates: {report.get('proposed_updates_count', 0)}",
        f"Applied updates: {report.get('applied_updates_count', 0)}",
        f"Reverted updates: {report.get('reverted_updates_count', 0)}",
        "",
        "Most corrected: " + ", ".join(report.get("most_corrected_ids", [])[:5]) or "—",
        "",
    ]
    if report.get("proposed_updates"):
        lines.append("Proposed (sample):")
        for u in report["proposed_updates"][:5]:
            lines.append(f"  {u.get('update_id')}  {u.get('target_type')}:{u.get('target_id')}")
        lines.append("")
    return "\n".join(lines)

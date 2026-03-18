"""
M40L.1: Operator-facing ongoing production summary — review cycle, checkpoint, guidance, metrics.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.production_launch.review_cycles import (
    build_production_review_cycle,
    get_latest_review_cycle,
)
from workflow_dataset.production_launch.sustained_use import (
    build_sustained_use_checkpoint,
    list_sustained_use_checkpoints,
)
from workflow_dataset.production_launch.post_deployment_guidance import build_post_deployment_guidance
from workflow_dataset.production_launch.decision_pack import build_launch_decision_pack


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def build_ongoing_production_summary(repo_root: Path | str | None = None) -> dict[str, Any]:
    """
    Build operator-facing ongoing production summary: current review snapshot, latest recorded cycle,
    latest checkpoint, post-deployment guidance, launch decision summary, key metrics.
    """
    root = _repo_root(repo_root)
    current_review = build_production_review_cycle(root)
    latest_cycle = get_latest_review_cycle(root)
    current_checkpoint = build_sustained_use_checkpoint(root, kind="auto")
    recorded_checkpoints = list_sustained_use_checkpoints(root, limit=5)
    guidance = build_post_deployment_guidance(root)
    pack = build_launch_decision_pack(root)

    return {
        "generated_at_iso": current_review["cycle"]["at_iso"],
        "vertical_id": pack.get("chosen_vertical_summary", {}).get("active_vertical_id", ""),
        "post_deployment_guidance": {
            "guidance": guidance["guidance"],
            "reason": guidance["reason"],
            "recommended_actions": guidance["recommended_actions"],
        },
        "current_review_cycle": current_review["cycle"],
        "launch_decision_summary": current_review.get("launch_decision_summary", {}),
        "latest_recorded_cycle": latest_cycle,
        "current_sustained_use_checkpoint": current_checkpoint["checkpoint"],
        "checkpoint_criteria_met": current_checkpoint.get("criteria_met", False),
        "recorded_checkpoints_count": len(recorded_checkpoints),
        "recorded_checkpoints_sample": recorded_checkpoints[:3],
        "key_metrics": {
            "blocker_count": len(pack.get("open_blockers", [])),
            "warning_count": len(pack.get("open_warnings", [])),
            "failed_gates_count": len([g for g in pack.get("release_gate_results", []) if not g.get("passed")]),
            "recommended_decision": pack.get("recommended_decision", "pause"),
        },
        "one_liner": _format_one_liner(guidance, pack, current_checkpoint),
    }


def _format_one_liner(
    guidance: dict[str, Any],
    pack: dict[str, Any],
    checkpoint: dict[str, Any],
) -> str:
    g = guidance.get("guidance", "continue")
    blockers = len(pack.get("open_blockers", []))
    met = checkpoint.get("criteria_met", False)
    return f"Guidance={g} Blockers={blockers} Sustained-use criteria_met={met}. Run production-runbook ongoing-summary for full report."


def format_ongoing_summary_report(summary: dict[str, Any]) -> str:
    """Format ongoing production summary as plain text for console."""
    lines = [
        "=== Ongoing production summary (operator) ===",
        "",
        summary.get("one_liner", ""),
        "",
        "[Post-deployment guidance]",
        f"  {summary.get('post_deployment_guidance', {}).get('guidance', '—')}: {summary.get('post_deployment_guidance', {}).get('reason', '')[:80]}",
        "  Recommended actions:",
    ]
    for a in summary.get("post_deployment_guidance", {}).get("recommended_actions", [])[:5]:
        lines.append(f"    - {a}")
    lines.append("")
    lines.append("[Current review cycle snapshot]")
    cy = summary.get("current_review_cycle", {})
    lines.append(f"  {cy.get('at_iso', '—')}  guidance_snapshot={cy.get('guidance_snapshot', '—')}")
    lines.append(f"  Summary: {cy.get('summary', '')[:100]}")
    if cy.get("findings"):
        for f in cy["findings"][:5]:
            lines.append(f"  Finding: {f}")
    lines.append("")
    lines.append("[Sustained-use checkpoint]")
    cp = summary.get("current_sustained_use_checkpoint", {})
    lines.append(f"  kind={cp.get('kind', '—')}  criteria_met={cp.get('criteria_met')}  guidance={cp.get('guidance', '—')}")
    lines.append(f"  {cp.get('report_summary', '')[:100]}")
    lines.append("")
    lines.append("[Key metrics]")
    km = summary.get("key_metrics", {})
    lines.append(f"  Blockers={km.get('blocker_count', 0)}  Warnings={km.get('warning_count', 0)}  Failed gates={km.get('failed_gates_count', 0)}  Launch decision={km.get('recommended_decision', '—')}")
    return "\n".join(lines)

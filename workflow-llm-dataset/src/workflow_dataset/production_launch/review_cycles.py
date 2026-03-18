"""
M40L.1: Production review cycles — build snapshot, record, list, latest.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from workflow_dataset.production_launch.models import ProductionReviewCycle
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


def _cycles_path(root: Path) -> Path:
    return root / "data/local/production_launch/review_cycles.json"


def build_production_review_cycle(repo_root: Path | str | None = None) -> dict[str, Any]:
    """
    Build current production review cycle snapshot: state + post-deployment guidance + findings.
    Does not persist; use record_review_cycle to save.
    """
    root = _repo_root(repo_root)
    now = datetime.now(timezone.utc)
    at_iso = now.isoformat()[:19] + "Z"

    pack = build_launch_decision_pack(root)
    guidance_result = build_post_deployment_guidance(root)
    guidance = guidance_result.get("guidance", "continue")
    recommended_actions = guidance_result.get("recommended_actions", [])

    findings: list[str] = []
    if pack.get("open_blockers"):
        findings.append(f"Blockers: {len(pack['open_blockers'])} — {pack['open_blockers'][0].get('summary', '')[:60]}")
    if pack.get("open_warnings"):
        findings.append(f"Warnings: {len(pack['open_warnings'])}")
    failed_gates = [g for g in pack.get("release_gate_results", []) if not g.get("passed")]
    if failed_gates:
        findings.append(f"Failed gates: {len(failed_gates)} — {failed_gates[0].get('gate_id', '')}")
    if guidance_result.get("evidence", {}).get("open_issue_count", 0) > 0:
        findings.append(f"Open triage issues: {guidance_result['evidence']['open_issue_count']} (highest: {guidance_result['evidence'].get('highest_severity', '—')})")

    summary = f"Guidance={guidance}. Blockers={len(pack.get('open_blockers', []))} Warnings={len(pack.get('open_warnings', []))} Failed gates={len(failed_gates)}."
    next_due = (now + timedelta(days=7)).isoformat()[:10] + "T00:00:00Z"

    cycle = ProductionReviewCycle(
        cycle_id=at_iso.replace(":", "-").replace(" ", "T")[:20],
        at_iso=at_iso,
        summary=summary,
        findings=findings,
        guidance_snapshot=guidance,
        recommended_actions=recommended_actions,
        next_due_iso=next_due,
        vertical_id=pack.get("chosen_vertical_summary", {}).get("active_vertical_id", ""),
    )
    return {
        "cycle": cycle.to_dict(),
        "launch_decision_summary": {
            "recommended_decision": pack.get("recommended_decision"),
            "blocker_count": len(pack.get("open_blockers", [])),
            "warning_count": len(pack.get("open_warnings", [])),
        },
        "post_deployment_guidance": guidance_result,
    }


def record_review_cycle(repo_root: Path | str | None = None) -> Path:
    """Append current review cycle to review_cycles.json; return path to file."""
    root = _repo_root(repo_root)
    data = build_production_review_cycle(root)
    path = _cycles_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    cycles: list[dict[str, Any]] = []
    if path.exists():
        try:
            cycles = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(cycles, list):
                cycles = []
        except Exception:
            cycles = []
    cycles.append(data["cycle"])
    path.write_text(json.dumps(cycles, indent=2), encoding="utf-8")
    return path


def list_review_cycles(repo_root: Path | str | None = None, limit: int = 20) -> list[dict[str, Any]]:
    """List recorded review cycles (newest first)."""
    root = _repo_root(repo_root)
    path = _cycles_path(root)
    if not path.exists():
        return []
    try:
        cycles = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(cycles, list):
            return []
        return list(reversed(cycles[-limit:]))
    except Exception:
        return []


def get_latest_review_cycle(repo_root: Path | str | None = None) -> dict[str, Any] | None:
    """Return most recent recorded review cycle or None."""
    cycles = list_review_cycles(repo_root, limit=1)
    return cycles[0] if cycles else None

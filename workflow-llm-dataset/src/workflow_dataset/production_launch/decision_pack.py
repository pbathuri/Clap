"""
M40K: Launch decision pack — assemble vertical summary, gate results, blockers/warnings, recovery/trust/support posture, recommended decision.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.production_launch.models import (
    LaunchBlocker,
    LaunchDecision,
    LaunchGateResult,
    LaunchWarning,
)
from workflow_dataset.production_launch.gates import evaluate_production_gates


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def build_launch_decision_pack(repo_root: Path | str | None = None) -> dict[str, Any]:
    """
    Build launch decision pack from current product state. Includes:
    - chosen_vertical_summary, supported_scope
    - release_gate_results, open_blockers, open_warnings
    - recovery_posture, trust_posture, support_posture
    - recommended_decision (launch | launch_narrowly | pause | repair_and_review)
    - explain (why)
    """
    root = _repo_root(repo_root)
    pack: dict[str, Any] = {
        "chosen_vertical_summary": {},
        "supported_scope": {},
        "release_gate_results": [],
        "open_blockers": [],
        "open_warnings": [],
        "recovery_posture": "",
        "trust_posture": "",
        "support_posture": "",
        "recommended_decision": LaunchDecision.PAUSE.value,
        "explain": "",
    }

    # Chosen vertical and scope
    try:
        from workflow_dataset.vertical_selection import get_active_vertical_id, get_scope_report
        vid = get_active_vertical_id(root)
        pack["chosen_vertical_summary"] = {"active_vertical_id": vid, "label": vid or "none"}
        if vid:
            scope = get_scope_report(vid)
            if scope:
                pack["supported_scope"] = scope if isinstance(scope, dict) else {}
    except Exception as e:
        pack["chosen_vertical_summary"] = {"error": str(e)}
        pack["supported_scope"] = {}

    # Gate results
    gate_results = evaluate_production_gates(root)
    pack["release_gate_results"] = [g.to_dict() for g in gate_results]
    failed_gates = [g for g in gate_results if not g.passed]

    # Blockers and warnings from release readiness + failed production gates
    blockers: list[LaunchBlocker] = []
    warnings: list[LaunchWarning] = []
    try:
        from workflow_dataset.release_readiness.readiness import build_release_readiness
        rr = build_release_readiness(root)
        for b in rr.blockers:
            blockers.append(LaunchBlocker(id=b.id, summary=b.summary, source=b.source or "release_readiness", remediation_hint=b.remediation_hint or "", severity="blocker"))
        for w in rr.warnings:
            warnings.append(LaunchWarning(id=w.id, summary=w.summary, source=w.source or "release_readiness"))
    except Exception as e:
        blockers.append(LaunchBlocker(id="readiness_error", summary=str(e), source="release_readiness", remediation_hint="Run workflow-dataset release readiness.", severity="blocker"))

    for g in failed_gates:
        if g.gate_id in ("release_readiness_not_blocked", "upgrade_recovery_posture", "trust_review_posture", "reliability_golden_path_health_acceptable", "chosen_vertical_first_value_proof_acceptable"):
            blockers.append(LaunchBlocker(
                id=f"gate_{g.gate_id}",
                summary=g.detail or g.label,
                source="production_gates",
                remediation_hint=f"Address gate: {g.label}",
                severity="blocker",
            ))
        else:
            warnings.append(LaunchWarning(id=f"gate_{g.gate_id}", summary=g.detail or g.label, source="production_gates"))

    pack["open_blockers"] = [b.to_dict() for b in blockers]
    pack["open_warnings"] = [w.to_dict() for w in warnings]

    # Recovery / trust / support posture (short summaries)
    try:
        from workflow_dataset.release_readiness.readiness import build_release_readiness
        rr = build_release_readiness(root)
        pack["recovery_posture"] = "Recovery guide and vertical recovery paths available; run workflow-dataset recovery guide / vertical-packs recovery."
        pack["trust_posture"] = f"Trust cockpit: registry_exists checked; supportability guidance={rr.supportability.guidance or '—'}"
        pack["support_posture"] = rr.supportability.recommended_next_support_action or "workflow-dataset release triage"
    except Exception:
        pack["recovery_posture"] = "Unknown; run workflow-dataset release readiness."
        pack["trust_posture"] = "Unknown"
        pack["support_posture"] = "workflow-dataset release triage"

    # Recommended decision: evidence-based
    if blockers:
        pack["recommended_decision"] = LaunchDecision.REPAIR_AND_REVIEW.value
        pack["explain"] = f"Blockers present ({len(blockers)}): {blockers[0].summary[:80]}. Resolve blockers then re-run launch-decision-pack."
    elif failed_gates and not blockers:
        # Gates failed but we didn't add them as blockers (e.g. optional gates)
        critical_failures = [g for g in failed_gates if g.gate_id in (
            "release_readiness_not_blocked", "upgrade_recovery_posture", "trust_review_posture",
            "reliability_golden_path_health_acceptable", "chosen_vertical_first_value_proof_acceptable")]
        if critical_failures:
            pack["recommended_decision"] = LaunchDecision.REPAIR_AND_REVIEW.value
            pack["explain"] = f"Critical gate(s) failed: {critical_failures[0].label}. {critical_failures[0].detail}"
        elif warnings:
            pack["recommended_decision"] = LaunchDecision.LAUNCH_NARROWLY.value
            pack["explain"] = f"Gates pass with {len(warnings)} warning(s). Launch narrowly; monitor."
        else:
            pack["recommended_decision"] = LaunchDecision.LAUNCH.value
            pack["explain"] = "All production gates passed. No blockers."
    elif warnings:
        pack["recommended_decision"] = LaunchDecision.LAUNCH_NARROWLY.value
        pack["explain"] = f"All gates passed. {len(warnings)} warning(s): launch narrowly; monitor."
    else:
        pack["recommended_decision"] = LaunchDecision.LAUNCH.value
        pack["explain"] = "All production gates passed. No blockers or warnings."

    return pack


def explain_launch_decision(pack: dict[str, Any] | None = None, repo_root: Path | str | None = None) -> str:
    """Return human-readable explanation of the launch decision (why launch / pause / repair)."""
    if pack is None:
        pack = build_launch_decision_pack(repo_root)
    lines = [
        f"Recommended decision: {pack.get('recommended_decision', 'pause')}",
        pack.get("explain", ""),
        "",
        f"Blockers: {len(pack.get('open_blockers', []))}",
        f"Warnings: {len(pack.get('open_warnings', []))}",
    ]
    failed = [g for g in pack.get("release_gate_results", []) if not g.get("passed")]
    if failed:
        lines.append(f"Failed gates: {len(failed)}")
        for g in failed[:5]:
            lines.append(f"  - {g.get('gate_id', '')}: {g.get('detail', '')}")
    if pack.get("open_blockers"):
        lines.append("Top blocker: " + (pack["open_blockers"][0].get("summary", "")[:100]))
    return "\n".join(lines)


def write_launch_decision_pack_to_dir(
    repo_root: Path | str | None = None,
    output_dir: Path | str | None = None,
) -> Path:
    """Write launch decision pack JSON to output_dir (default data/local/production_launch). Returns path to written file."""
    root = _repo_root(repo_root)
    if output_dir is None:
        output_dir = root / "data/local/production_launch"
    out = Path(output_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    pack = build_launch_decision_pack(root)
    import json
    path = out / "launch_decision_pack.json"
    path.write_text(json.dumps(pack, indent=2), encoding="utf-8")
    return path

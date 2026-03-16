"""
M23V: Format trust cockpit and release gates as text.
"""

from __future__ import annotations

from typing import Any

from workflow_dataset.trust.cockpit import build_trust_cockpit


def format_trust_cockpit(cockpit: dict[str, Any] | None = None, repo_root=None) -> str:
    """Produce human-readable trust cockpit report."""
    if cockpit is None:
        cockpit = build_trust_cockpit(repo_root)
    lines = [
        "=== Trust / evidence cockpit ===",
        "",
    ]
    if cockpit.get("errors"):
        lines.append("[Errors] " + "; ".join(cockpit["errors"][:5]))
        lines.append("")

    bt = cockpit.get("benchmark_trust") or {}
    lines.append("[Benchmark trust]")
    lines.append(f"  latest_run: {bt.get('latest_run_id')}  outcome: {bt.get('latest_outcome')}  trust_status: {bt.get('latest_trust_status')}")
    lines.append(f"  simulate_only_coverage: {cockpit.get('simulate_only_coverage')}  trusted_real_coverage: {cockpit.get('trusted_real_coverage')}")
    if bt.get("missing_approval_blockers"):
        lines.append("  missing_approval_blockers: " + ", ".join(bt["missing_approval_blockers"]))
    if bt.get("regressions"):
        lines.append("  regressions: " + ", ".join(bt["regressions"]))
    lines.append(f"  next: {bt.get('recommended_next_action', '')}")
    lines.append("")

    ar = cockpit.get("approval_readiness") or {}
    lines.append("[Approval readiness]")
    lines.append(f"  registry_exists: {ar.get('registry_exists')}  path: {ar.get('registry_path', '')}")
    lines.append(f"  approved_paths: {ar.get('approved_paths_count', 0)}  approved_action_scopes: {ar.get('approved_action_scopes_count', 0)}")
    lines.append("")

    jm = cockpit.get("job_macro_trust_state") or {}
    lines.append("[Job / macro trust state]")
    lines.append(f"  total_jobs: {jm.get('total_jobs', 0)}  simulate_only: {jm.get('simulate_only_count', 0)}  trusted_for_real: {jm.get('trusted_for_real_count', 0)}  approval_blocked: {jm.get('approval_blocked_count', 0)}")
    lines.append(f"  recent_successful: {jm.get('recent_successful_count', 0)}  routines: {jm.get('routines_count', 0)}")
    lines.append("")

    uc = cockpit.get("unresolved_corrections") or {}
    lines.append("[Unresolved corrections]")
    lines.append(f"  proposed_updates: {uc.get('proposed_updates_count', 0)}")
    if uc.get("review_recommended_ids"):
        lines.append("  review_recommended: " + ", ".join(uc["review_recommended_ids"][:5]))
    lines.append("")

    rg = cockpit.get("release_gate_status") or {}
    lines.append("[Release gate status]")
    lines.append(f"  unreviewed: {rg.get('unreviewed_count', 0)}  package_pending: {rg.get('package_pending_count', 0)}  staged: {rg.get('staged_count', 0)}")
    lines.append(f"  release_readiness_report_exists: {rg.get('release_readiness_report_exists')}")
    lines.append("")
    lines.append("(Operator-controlled. No automatic changes.)")
    return "\n".join(lines)


def format_release_gates(cockpit: dict[str, Any] | None = None, repo_root=None) -> str:
    """Produce release-gate-only summary."""
    if cockpit is None:
        cockpit = build_trust_cockpit(repo_root)
    rg = cockpit.get("release_gate_status") or {}
    lines = [
        "=== Release gates ===",
        "",
        f"Unreviewed workspaces: {rg.get('unreviewed_count', 0)}",
        f"Package pending: {rg.get('package_pending_count', 0)}",
        f"Staged items: {rg.get('staged_count', 0)}",
        f"Release readiness report: {'present' if rg.get('release_readiness_report_exists') else 'missing'}",
        "",
    ]
    return "\n".join(lines)

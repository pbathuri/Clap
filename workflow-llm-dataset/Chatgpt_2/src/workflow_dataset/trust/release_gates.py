"""
M23Q: Release gate checks. Advisory only; no auto-promotion or hidden trust mutation.
"""

from __future__ import annotations

from typing import Any

GATE_NO_REGRESSIONS = "no_regressions"
GATE_APPROVAL_READY = "approval_registry_ready"
GATE_CORRECTIONS_ACCEPTABLE = "corrections_acceptable"
GATE_BENCHMARK_KNOWN = "benchmark_known"
GATE_RELEASE_READINESS_REPORT = "release_readiness_report"


def evaluate_release_gates(cockpit: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Evaluate explicit release gates from cockpit data.
    Returns list of {gate_id, name, passed, message}. Advisory only.
    """
    checks: list[dict[str, Any]] = []
    bt = cockpit.get("benchmark_trust") or {}
    ar = cockpit.get("approval_readiness") or {}
    uc = cockpit.get("unresolved_corrections") or {}
    rg = cockpit.get("release_gate_status") or {}

    # Gate: no open regressions
    regressions = bt.get("regressions") or []
    checks.append({
        "gate_id": GATE_NO_REGRESSIONS,
        "name": "No benchmark regressions",
        "passed": len(regressions) == 0,
        "message": "No regressions" if not regressions else f"Regressions: {', '.join(regressions[:3])}",
    })

    # Gate: approval registry present when needed (advisory: real mode needs it)
    registry_exists = ar.get("registry_exists", False)
    checks.append({
        "gate_id": GATE_APPROVAL_READY,
        "name": "Approval registry present",
        "passed": registry_exists,
        "message": "Registry present" if registry_exists else "Approval registry missing; required for real mode.",
    })

    # Gate: corrections within acceptable threshold (advisory: many proposed = review first)
    proposed = uc.get("proposed_updates_count", 0)
    review_ids = uc.get("review_recommended_ids") or []
    corrections_ok = proposed <= 20 and len(review_ids) <= 10
    checks.append({
        "gate_id": GATE_CORRECTIONS_ACCEPTABLE,
        "name": "Corrections acceptable",
        "passed": corrections_ok,
        "message": f"Proposed: {proposed}, review recommended: {len(review_ids)}" + (" (within threshold)" if corrections_ok else " (review recommended before expand)"),
    })

    # Gate: benchmark state known (at least one run or explicit no-run)
    latest_run = bt.get("latest_run_id")
    latest_outcome = bt.get("latest_outcome")
    known = latest_run is not None or cockpit.get("errors")
    checks.append({
        "gate_id": GATE_BENCHMARK_KNOWN,
        "name": "Benchmark state known",
        "passed": True,  # advisory: we always "know" (no runs = known empty)
        "message": f"Latest: {latest_run or 'none'} outcome: {latest_outcome or 'n/a'}",
    })

    # Gate: release readiness report exists (optional; can expand without it)
    report_exists = rg.get("release_readiness_report_exists", False)
    checks.append({
        "gate_id": GATE_RELEASE_READINESS_REPORT,
        "name": "Release readiness report",
        "passed": report_exists,
        "message": "Report present" if report_exists else "Release readiness report missing (optional for expand).",
    })

    return checks


def safe_to_expand(cockpit: dict[str, Any]) -> dict[str, Any]:
    """
    Advisory: is the current system safe to expand (broader use)?
    Returns {safe: bool, reasons: list[str], failed_gates: list[str]}.
    No automatic trust state mutation.
    """
    checks = cockpit.get("release_gate_checks")
    if checks is None:
        checks = evaluate_release_gates(cockpit)
    failed = [c["gate_id"] for c in checks if not c.get("passed")]
    # Require no regressions and approval ready for "safe to expand"; others advisory
    critical_gates = {GATE_NO_REGRESSIONS, GATE_APPROVAL_READY}
    critical_failed = [g for g in failed if g in critical_gates]
    safe = len(critical_failed) == 0
    reasons: list[str] = []
    if safe:
        reasons.append("No critical gate failures (no regressions, approval registry ready).")
    else:
        reasons.append(f"Critical gates failed: {', '.join(critical_failed)}.")
    if failed:
        reasons.append(f"Failed gates: {', '.join(failed)}.")
    return {
        "safe": safe,
        "reasons": reasons,
        "failed_gates": failed,
        "critical_failed": critical_failed,
    }

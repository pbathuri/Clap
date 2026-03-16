"""
M23I: Transparent scoring and trust signals for desktop benchmark runs.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

TRUST_STATUSES = (
    "trusted",
    "usable_with_simulation_only",
    "approval_missing",
    "experimental",
    "regression_detected",
)


def score_run(run_path: Path | str) -> dict[str, Any]:
    """
    Score a desktop benchmark run from its manifest. Returns manifest with added scores and trust_status.
    Transparent: approval_correctness, simulate_correctness, real_run_correctness, parity, artifact_completeness, provenance_completeness.
    """
    run_path = Path(run_path)
    manifest_path = run_path / "run_manifest.json"
    if not manifest_path.exists():
        return {}
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        return {}

    mode = manifest.get("mode", "simulate")
    outcome = manifest.get("outcome", "fail")
    approvals = manifest.get("approvals_checked") or {}
    case_result = manifest.get("case_result") or {}
    steps = case_result.get("steps") or []
    errors = manifest.get("errors") or []
    output_artifacts = manifest.get("output_artifacts") or []

    scores: dict[str, float] = {}
    # Approval correctness: registry present when real, and used
    if mode == "real":
        scores["approval_correctness"] = 1.0 if approvals.get("registry_exists") and not errors else (0.5 if approvals.get("registry_exists") else 0.0)
    else:
        scores["approval_correctness"] = 1.0  # N/A for simulate
    # Simulate correctness: all steps success in simulate
    if mode == "simulate":
        success_count = sum(1 for s in steps if s.get("success"))
        scores["simulate_correctness"] = (success_count / len(steps)) if steps else 1.0
    else:
        scores["simulate_correctness"] = 0.0  # N/A for real-only run
    # Real-run correctness: all steps success in real
    if mode == "real":
        success_count = sum(1 for s in steps if s.get("success"))
        scores["real_run_correctness"] = (success_count / len(steps)) if steps else 1.0
    else:
        scores["real_run_correctness"] = 0.0  # N/A
    # Parity: (for runs that have both simulate and real we'd compare; single-mode run has no parity)
    scores["simulate_real_parity"] = 0.0  # Reserved for compare runs
    # Artifact completeness: expected vs produced (we don't have expected in manifest easily; use presence)
    scores["artifact_completeness"] = 1.0 if (outcome == "pass" and output_artifacts) or outcome == "pass" else (0.5 if output_artifacts else 0.0)
    # Provenance completeness: manifest has approvals_checked and case_result
    scores["provenance_completeness"] = 1.0 if approvals and case_result else 0.5

    manifest["scores"] = scores
    manifest["trust_status"] = compute_trust_status(manifest, scores)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def compute_trust_status(manifest: dict[str, Any], scores: dict[str, float] | None = None) -> str:
    """
    Return one of: trusted | usable_with_simulation_only | approval_missing | experimental | regression_detected.
    Transparent logic; no hidden judgment.
    """
    mode = manifest.get("mode", "simulate")
    outcome = manifest.get("outcome", "fail")
    approvals = manifest.get("approvals_checked") or {}
    scores = scores or manifest.get("scores") or {}

    if outcome != "pass":
        return "experimental"

    if mode == "real":
        if not approvals.get("registry_exists"):
            return "approval_missing"
        if scores.get("real_run_correctness", 0) >= 1.0 and scores.get("approval_correctness", 0) >= 1.0:
            return "trusted"
        return "experimental"

    # Simulate pass
    if scores.get("simulate_correctness", 0) >= 1.0:
        if not approvals.get("registry_exists") or not manifest.get("real_mode_eligibility", False):
            return "usable_with_simulation_only"
        return "experimental"
    return "experimental"

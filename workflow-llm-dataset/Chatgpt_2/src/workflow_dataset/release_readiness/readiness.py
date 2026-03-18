"""
M30I–M30L: Build release readiness status from rollout, package_readiness, env, acceptance.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.release_readiness.models import (
    ReleaseReadinessStatus,
    ReleaseBlocker,
    ReleaseWarning,
    SupportedWorkflowScope,
    KnownLimitation,
    SupportabilityStatus,
    READINESS_READY,
    READINESS_BLOCKED,
    READINESS_DEGRADED,
    GUIDANCE_SAFE_TO_CONTINUE,
    GUIDANCE_NEEDS_OPERATOR,
    GUIDANCE_NEEDS_ROLLBACK,
)


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def build_release_readiness(repo_root: Path | str | None = None) -> ReleaseReadinessStatus:
    """
    Build release readiness status from rollout readiness, package_readiness, env health, acceptance.
    Returns ReleaseReadinessStatus (ready | blocked | degraded) with blockers, warnings, scope, limitations, supportability.
    """
    root = _repo_root(repo_root)
    blockers: list[ReleaseBlocker] = []
    warnings: list[ReleaseWarning] = []
    reasons: list[str] = []

    # Rollout readiness
    try:
        from workflow_dataset.rollout.readiness import build_rollout_readiness_report
        r = build_rollout_readiness_report(root)
        if not r.get("first_user_ready"):
            for b in (r.get("blocks") or [])[:10]:
                blockers.append(ReleaseBlocker(id=f"block_{len(blockers)}", summary=b, source="rollout", remediation_hint="Run workflow-dataset rollout status and address blocks."))
            for a in (r.get("operator_actions") or [])[:5]:
                reasons.append(a)
        if r.get("first_user_ready"):
            reasons.append("Rollout: first_user_ready.")
        for e in (r.get("experimental") or [])[:5]:
            warnings.append(ReleaseWarning(id=f"exp_{len(warnings)}", summary=str(e), source="rollout"))
    except Exception as e:
        blockers.append(ReleaseBlocker(id="rollout_error", summary=str(e), source="rollout_readiness", remediation_hint="Run workflow-dataset rollout status."))

    # Package readiness
    try:
        from workflow_dataset.package_readiness.summary import build_readiness_summary
        pkg = build_readiness_summary(root)
        if not pkg.get("ready_for_first_real_user_install"):
            for r in (pkg.get("not_ready_reasons") or [])[:5]:
                blockers.append(ReleaseBlocker(id=f"pkg_{len(blockers)}", summary=r, source="package_readiness", remediation_hint="Run workflow-dataset package readiness-report."))
        if pkg.get("ready_for_first_real_user_install"):
            reasons.append("Package: ready for first real-user install.")
    except Exception as e:
        warnings.append(ReleaseWarning(id="pkg_error", summary=str(e), source="package_readiness"))

    # Environment
    try:
        from workflow_dataset.validation.env_health import check_environment_health
        env = check_environment_health(root)
        if not env.get("required_ok", True):
            blockers.append(ReleaseBlocker(id="env_required", summary="Environment required checks failed.", source="env_health", remediation_hint="Run workflow-dataset health."))
    except Exception as e:
        warnings.append(ReleaseWarning(id="env_error", summary=str(e), source="env_health"))

    # Supported scope (default from release reporting workflows if available)
    try:
        from workflow_dataset.release.reporting_workspaces import REPORTING_WORKFLOWS
        workflow_ids = list(REPORTING_WORKFLOWS)[:20]
    except Exception:
        workflow_ids = []
    supported_scope = SupportedWorkflowScope(workflow_ids=workflow_ids, description="First-user release supports workflows listed in release reporting_workspaces.")

    # Known limitations (first-draft static list; can be extended from config)
    known_limitations = [
        KnownLimitation(id="manual_approval", summary="Approval and trust gates require operator action; no unattended real execution.", category="manual_step"),
        KnownLimitation(id="local_first", summary="All state is local-first; no built-in cloud sync or ticketing.", category="scope"),
    ]

    # Supportability: derive from blockers
    if blockers:
        status = READINESS_BLOCKED
        supportability = SupportabilityStatus(
            confidence="low",
            guidance=GUIDANCE_NEEDS_OPERATOR,
            recommended_next_support_action="Resolve release blockers; run 'workflow-dataset release readiness' and address listed blocks.",
        )
    else:
        if warnings:
            status = READINESS_DEGRADED
            supportability = SupportabilityStatus(
                confidence="medium",
                guidance=GUIDANCE_NEEDS_OPERATOR,
                recommended_next_support_action="Review warnings; run 'workflow-dataset release supportability'.",
            )
        else:
            status = READINESS_READY
            supportability = SupportabilityStatus(
                confidence="high",
                guidance=GUIDANCE_SAFE_TO_CONTINUE,
                recommended_next_support_action="Release readiness OK; run 'workflow-dataset release pack' for user release pack.",
            )

    return ReleaseReadinessStatus(
        status=status,
        blockers=blockers,
        warnings=warnings,
        supported_scope=supported_scope,
        known_limitations=known_limitations,
        supportability=supportability,
        reasons=reasons,
    )


def format_release_readiness_report(repo_root: Path | str | None = None) -> str:
    """Produce a readable release readiness report."""
    r = build_release_readiness(repo_root)
    lines = [
        "=== Release readiness (first-user) ===",
        "",
        "[Status] " + r.status.upper(),
        "",
        "[Blockers]",
    ]
    for b in r.blockers:
        lines.append(f"  - {b.summary} (source: {b.source})")
    if not r.blockers:
        lines.append("  (none)")
    lines.append("")
    lines.append("[Warnings]")
    for w in r.warnings:
        lines.append(f"  - {w.summary}")
    if not r.warnings:
        lines.append("  (none)")
    lines.append("")
    lines.append("[Supported workflows] " + ", ".join(r.supported_scope.workflow_ids[:8]) or "(see release reporting_workspaces)")
    lines.append("")
    lines.append("[Known limitations]")
    for k in r.known_limitations:
        lines.append(f"  - {k.summary}")
    lines.append("")
    lines.append("[Supportability] " + r.supportability.confidence + "  guidance: " + r.supportability.guidance)
    lines.append("  next: " + r.supportability.recommended_next_support_action)
    return "\n".join(lines)

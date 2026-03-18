"""
M30I–M30L: User release pack — install profile, first-run guide, quickstart, supported workflows, limitations, trust, recovery, diagnostics refs.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.release_readiness.readiness import build_release_readiness


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def build_user_release_pack(repo_root: Path | str | None = None) -> dict[str, Any]:
    """
    Build first-draft user release pack: install profile ref, first-run guide, quickstart path,
    supported workflows, known limitations, trust/approval explanation, recovery/support refs, diagnostics refs.
    """
    root = _repo_root(repo_root)
    readiness = build_release_readiness(root)

    # Install profile: point to onboarding/install flow or edge profile if present
    install_profile = "Onboarding and edge readiness define install profile. Run: workflow-dataset onboard status ; workflow-dataset edge readiness."

    # First-run guide
    first_run_guide = "docs/onboarding or quickstart. Run: workflow-dataset quickstart quickref."

    # Quickstart path
    try:
        from workflow_dataset.operator_quickstart import build_quick_reference
        build_quick_reference()
        quickstart_path = "workflow-dataset quickstart quickref (and first_value_flow if used)"
    except Exception:
        quickstart_path = "workflow-dataset quickstart quickref"

    # Supported workflows
    supported_workflows = list(readiness.supported_scope.workflow_ids) or ["See release reporting_workspaces"]

    # Known limitations (from readiness model)
    known_limitations = [k.summary for k in readiness.known_limitations]

    # Trust/approval posture
    trust_explanation = "Approvals and trust gates are required before real execution. Use data/local/capability_discovery/approvals (or trust cockpit). Run: workflow-dataset trust report."

    # Recovery/support refs
    recovery_refs = [
        "workflow-dataset progress recovery --project <id>",
        "docs/rollout/OPERATOR_RUNBOOKS.md",
        "docs/rollout/RECOVERY_ESCALATION.md",
        "workflow-dataset rollout status",
    ]

    # Diagnostics bundle refs
    diagnostics_refs = [
        "workflow-dataset rollout support-bundle (writes to data/local/rollout/support_bundle_*)",
        "workflow-dataset release supportability",
        "workflow-dataset mission-control",
    ]

    return {
        "install_profile": install_profile,
        "first_run_guide": first_run_guide,
        "quickstart_path": quickstart_path,
        "supported_workflows": supported_workflows,
        "known_limitations": known_limitations,
        "trust_explanation": trust_explanation,
        "recovery_refs": recovery_refs,
        "diagnostics_refs": diagnostics_refs,
        "readiness_status": readiness.status,
        "generated_at": _now_iso(),
    }


def _now_iso() -> str:
    try:
        from workflow_dataset.utils.dates import utc_now_iso
        return utc_now_iso()
    except Exception:
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()


def format_user_release_pack(repo_root: Path | str | None = None) -> str:
    """Format user release pack as readable text."""
    p = build_user_release_pack(repo_root)
    lines = [
        "=== User release pack (first-user) ===",
        "",
        "[Install profile]",
        "  " + p["install_profile"],
        "",
        "[First-run guide]",
        "  " + p["first_run_guide"],
        "",
        "[Quickstart path]",
        "  " + p["quickstart_path"],
        "",
        "[Supported workflows]",
    ]
    for w in (p.get("supported_workflows") or [])[:15]:
        lines.append("  - " + str(w))
    lines.append("")
    lines.append("[Known limitations]")
    for k in p.get("known_limitations") or []:
        lines.append("  - " + str(k))
    lines.append("")
    lines.append("[Trust/approval]")
    lines.append("  " + p.get("trust_explanation", ""))
    lines.append("")
    lines.append("[Recovery/support refs]")
    for r in p.get("recovery_refs") or []:
        lines.append("  - " + str(r))
    lines.append("")
    lines.append("[Diagnostics]")
    for d in p.get("diagnostics_refs") or []:
        lines.append("  - " + str(d))
    lines.append("")
    lines.append("Readiness: " + p.get("readiness_status", "") + "  generated: " + p.get("generated_at", ""))
    return "\n".join(lines)

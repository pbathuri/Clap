"""
M24R–M24U: Field deployment checklists — per-pack runtime prereqs, pack provisioning,
trust/readiness checks, first-value run after install.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.distribution.install_profile import (
    build_field_deployment_profile,
    PACK_DEFAULTS,
)


def _repo_root(root: Path | str | None) -> Path:
    if root is not None:
        return Path(root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


CHECKLIST_PACK_IDS = ["founder_ops_starter", "analyst_starter", "developer_starter", "document_worker_starter"]
# Alias for checklist --pack (founder_ops_plus -> founder_ops_starter)
CHECKLIST_PACK_ALIASES = {"founder_ops_plus": "founder_ops_starter"}


def build_field_checklist(
    pack_id: str,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """Build field deployment checklist for pack_id. Includes runtime prereqs, pack provisioning, trust/readiness, first-value run."""
    root = _repo_root(repo_root)
    actual_pack = CHECKLIST_PACK_ALIASES.get(pack_id, pack_id)
    profile = build_field_deployment_profile(actual_pack, root)
    checklist = {
        "pack_id": actual_pack,
        "pack_name": profile.pack_name,
        "runtime_prerequisites": profile.runtime_prerequisites,
        "pack_provisioning_prerequisites": profile.pack_provisioning_prerequisites,
        "trust_readiness_checks": profile.trust_readiness_checks,
        "first_value_run_command": profile.first_value_run_command,
        "first_value_run_notes": profile.first_value_run_notes,
        "required_capabilities": profile.required_capabilities,
        "required_approvals_setup": profile.required_approvals_setup,
        "commands": [
            "workflow-dataset package install-check",
            "workflow-dataset package first-run",
            "workflow-dataset onboarding status",
            "workflow-dataset kits recommend",
            "workflow-dataset rollout launch --id " + _demo_id_for_pack(actual_pack),
            "workflow-dataset trust cockpit",
            "workflow-dataset rollout readiness",
        ],
    }
    return checklist


def _demo_id_for_pack(pack_id: str) -> str:
    m = {
        "founder_ops_starter": "founder_demo",
        "analyst_starter": "analyst_demo",
        "developer_starter": "developer_demo",
        "document_worker_starter": "document_worker_demo",
    }
    return m.get(pack_id, "founder_demo")


def format_field_checklist(checklist: dict[str, Any]) -> str:
    """Human-readable checklist."""
    lines = [
        f"=== Field deployment checklist: {checklist.get('pack_name', checklist.get('pack_id', ''))} ===",
        "",
        "[Runtime prerequisites]",
    ]
    for r in checklist.get("runtime_prerequisites") or []:
        lines.append(f"  - {r}")
    lines.append("")
    lines.append("[Pack provisioning prerequisites]")
    for p in checklist.get("pack_provisioning_prerequisites") or []:
        lines.append(f"  - {p}")
    lines.append("")
    lines.append("[Trust / readiness checks]")
    for t in checklist.get("trust_readiness_checks") or []:
        lines.append(f"  - {t}")
    lines.append("")
    lines.append("[First-value run after install]")
    lines.append(f"  Command: {checklist.get('first_value_run_command', '—')}")
    lines.append(f"  Next: {checklist.get('first_value_run_notes', '—')}")
    lines.append("")
    lines.append("[Suggested commands (in order)]")
    for c in checklist.get("commands") or []:
        lines.append(f"  {c}")
    return "\n".join(lines)


def list_checklist_packs() -> list[str]:
    """Return list of pack IDs that have field checklists (includes aliases like founder_ops_plus)."""
    return list(CHECKLIST_PACK_IDS) + list(CHECKLIST_PACK_ALIASES.keys())

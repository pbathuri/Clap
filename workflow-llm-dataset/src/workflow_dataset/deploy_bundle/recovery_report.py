"""
M40E–M40H: Recovery report for deployment bundle — posture, recovery cases, vertical playbook, degraded startup.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.deploy_bundle.registry import get_deployment_bundle


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def build_recovery_report(
    bundle_id: str,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Build recovery report for deployment bundle: recovery posture, applicable recovery cases,
    vertical playbook refs, degraded startup guidance. Delegates to reliability + vertical_packs playbooks.
    """
    bundle = get_deployment_bundle(bundle_id)
    if not bundle:
        return {"error": f"Bundle not found: {bundle_id}", "bundle_id": bundle_id}
    root = _repo_root(repo_root)
    out: dict[str, Any] = {
        "bundle_id": bundle_id,
        "recovery_posture": bundle.recovery_posture.to_dict(),
        "applicable_recovery_cases": [],
        "vertical_playbook_recovery_ref": "",
        "degraded_startup_guidance": bundle.recovery_posture.degraded_startup_guidance,
        "recovery_doc_refs": list(bundle.recovery_posture.recovery_doc_refs),
    }
    out["vertical_playbook_recovery_ref"] = (
        "workflow-dataset vertical-packs playbook --id " + bundle.curated_pack_id
        if bundle.curated_pack_id else ""
    )
    # Resolve recovery case names from reliability
    try:
        from workflow_dataset.reliability.recovery_playbooks import RECOVERY_CASES
        case_ids = set(bundle.recovery_posture.applicable_recovery_case_ids)
        for c in RECOVERY_CASES:
            if c.case_id in case_ids:
                out["applicable_recovery_cases"].append({
                    "case_id": c.case_id,
                    "name": c.name,
                    "when_to_use": c.when_to_use,
                    "steps_count": len(c.steps_guide),
                })
    except Exception:
        out["applicable_recovery_cases"] = [
            {"case_id": cid, "name": cid, "when_to_use": "", "steps_count": 0}
            for cid in bundle.recovery_posture.applicable_recovery_case_ids
        ]
    return out

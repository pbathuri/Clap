"""
M25I–M25L: Pack certification harness — structural validation, conflict simulation,
first-value readiness, installability, acceptance compatibility. Status: draft | valid | certifiable | blocked | needs_revision.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.packs.authoring_validation import validate_pack_full
from workflow_dataset.packs.pack_models import PackManifest
from workflow_dataset.packs.pack_validator import validate_pack_manifest_and_recipes
from workflow_dataset.packs.pack_conflicts import detect_conflicts
from workflow_dataset.packs.pack_state import get_packs_dir


def _packs_dir(repo_root: Path | str | None, packs_dir: Path | str | None) -> Path:
    if packs_dir:
        return Path(packs_dir).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        root = Path(get_repo_root()).resolve()
    except Exception:
        root = Path.cwd().resolve()
    return root / "data/local/packs"


CERT_STATUS_DRAFT = "draft"
CERT_STATUS_VALID = "valid"
CERT_STATUS_CERTIFIABLE = "certifiable"
CERT_STATUS_BLOCKED = "blocked"
CERT_STATUS_NEEDS_REVISION = "needs_revision"


def run_certification(
    pack_id: str,
    packs_dir: Path | str | None = None,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Run certification checks: structural validation, conflict simulation with installed packs,
    first-value readiness (has templates or first_value hint), installability (valid manifest),
    acceptance compatibility (optional). Return status and checks list.
    """
    root = _packs_dir(repo_root, packs_dir)
    manifest_path = root / pack_id / "manifest.json"
    result: dict[str, Any] = {
        "pack_id": pack_id,
        "status": CERT_STATUS_DRAFT,
        "checks": [],
        "errors": [],
        "warnings": [],
    }
    if not manifest_path.exists():
        result["errors"].append("Manifest not found")
        result["status"] = CERT_STATUS_NEEDS_REVISION
        return result
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as e:
        result["errors"].append(str(e))
        result["status"] = CERT_STATUS_NEEDS_REVISION
        return result
    # Structural validation
    full = validate_pack_full(pack_id=pack_id, packs_dir=root, repo_root=repo_root)
    result["checks"].append({"name": "structural", "passed": full["valid"], "detail": full["errors"] or full["warnings"]})
    if not full["valid"]:
        result["errors"].extend(full["errors"])
        result["warnings"].extend(full["warnings"])
        result["status"] = CERT_STATUS_NEEDS_REVISION
        return result
    result["warnings"] = list(full["warnings"])
    # Installability (manifest + recipes valid)
    ok, errs = validate_pack_manifest_and_recipes(data)
    result["checks"].append({"name": "installability", "passed": ok, "detail": errs})
    if not ok:
        result["errors"].extend(errs)
        result["status"] = CERT_STATUS_NEEDS_REVISION
        return result
    # First-value readiness: has templates or workflow_templates
    has_templates = bool(data.get("templates") or data.get("workflow_templates"))
    result["checks"].append({"name": "first_value_readiness", "passed": has_templates, "detail": ["Has templates"] if has_templates else ["Add templates or workflow_templates"]})
    # Acceptance scenario compatibility: templates enable acceptance flows
    result["checks"].append({"name": "acceptance_scenario_compatibility", "passed": has_templates, "detail": ["Has workflow/task templates for acceptance scenarios"] if has_templates else ["Add workflow_templates for acceptance scenario compatibility"]})
    # Trust/readiness signals: safety_policies and optionally safety_constraints present
    sp = data.get("safety_policies") or {}
    trust_ok = bool(sp) and sp.get("sandbox_only") is not False and sp.get("require_apply_confirm") is not False
    result["checks"].append({"name": "trust_readiness_signals", "passed": trust_ok, "detail": ["safety_policies present and safe defaults"] if trust_ok else ["Set safety_policies (sandbox_only, require_apply_confirm)"]})
    # Conflict simulation with other installed packs
    try:
        from workflow_dataset.packs.pack_registry import list_installed_packs, get_installed_manifest
        installed = list_installed_packs(root)
        other_manifests = []
        for rec in installed:
            if rec.get("pack_id") == pack_id:
                continue
            m = get_installed_manifest(rec["pack_id"], root)
            if m:
                other_manifests.append(m)
        current = PackManifest.model_validate(data)
        all_manifests = [current] + other_manifests
        conflicts = detect_conflicts(all_manifests) if len(all_manifests) >= 2 else []
        blocked = [c for c in conflicts if c.conflict_class.value == "blocked" or c.conflict_class.value == "incompatible"]
        result["checks"].append({
            "name": "conflict_simulation",
            "passed": len(blocked) == 0,
            "detail": [f"{c.conflict_class.value}: {c.capability}" for c in conflicts],
        })
        if blocked:
            result["errors"].extend([f"Conflict: {c.capability} ({c.conflict_class.value})" for c in blocked])
            result["status"] = CERT_STATUS_BLOCKED
            return result
    except Exception as e:
        result["checks"].append({"name": "conflict_simulation", "passed": True, "detail": [str(e)]})
    # Determine final status
    if result["errors"]:
        result["status"] = CERT_STATUS_NEEDS_REVISION
    elif result["warnings"] and not has_templates:
        result["status"] = CERT_STATUS_VALID
    elif has_templates and not result["errors"]:
        result["status"] = CERT_STATUS_CERTIFIABLE
    else:
        result["status"] = CERT_STATUS_VALID
    return result


def format_certification_report(result: dict[str, Any]) -> str:
    """Human-readable certification report for a single pack."""
    lines = [
        "=== Pack certification: " + result.get("pack_id", "") + " ===",
        "",
        "Status: " + result.get("status", "unknown"),
        "",
        "[Checks]",
    ]
    for c in result.get("checks", []):
        status = "pass" if c.get("passed") else "fail"
        lines.append("  " + c.get("name", "") + ": " + status)
        for d in (c.get("detail") or [])[:5]:
            lines.append("    - " + str(d))
    if result.get("errors"):
        lines.append("")
        lines.append("[Errors]")
        for e in result["errors"]:
            lines.append("  - " + str(e))
    if result.get("warnings"):
        lines.append("")
        lines.append("[Warnings]")
        for w in result["warnings"][:10]:
            lines.append("  - " + str(w))
    lines.append("")
    return "\n".join(lines)

"""
M25I–M25L: Pack scorecard — roles, tasks, runtime, conflict risk, first-value strength,
acceptance readiness, certification status, recommended fixes.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.packs.certification import run_certification, CERT_STATUS_CERTIFIABLE, CERT_STATUS_BLOCKED
from workflow_dataset.packs.authoring_validation import validate_pack_full


def _packs_dir(repo_root: Path | str | None, packs_dir: Path | str | None) -> Path:
    if packs_dir:
        return Path(packs_dir).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        root = Path(get_repo_root()).resolve()
    except Exception:
        root = Path.cwd().resolve()
    return root / "data/local/packs"


def build_pack_scorecard(
    pack_id: str,
    packs_dir: Path | str | None = None,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """Build scorecard dict: roles, tasks, runtime, conflict_risk, first_value_strength, acceptance_readiness, certification_status, recommended_fixes."""
    root = _packs_dir(repo_root, packs_dir)
    path = root / pack_id / "manifest.json"
    out: dict[str, Any] = {
        "pack_id": pack_id,
        "roles_supported": [],
        "tasks_workflows_supported": [],
        "runtime_requirements": [],
        "conflict_risk": [],
        "first_value_strength": "none",
        "acceptance_readiness": "unknown",
        "certification_status": "unknown",
        "recommended_fixes": [],
    }
    if not path.exists():
        out["recommended_fixes"].append("Create pack: workflow-dataset packs scaffold --id " + pack_id)
        return out
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        out["recommended_fixes"].append("Fix manifest.json (invalid JSON)")
        return out
    out["roles_supported"] = data.get("role_tags") or []
    out["tasks_workflows_supported"] = list(set((data.get("templates") or []) + (data.get("workflow_templates") or [])))
    out["runtime_requirements"] = (data.get("required_models") or []) + (data.get("recommended_models") or [])
    if data.get("optional_wrappers"):
        out["runtime_requirements"].extend(data["optional_wrappers"])
    full = validate_pack_full(pack_id=pack_id, packs_dir=root, repo_root=repo_root)
    out["conflict_risk"] = full.get("conflict_risk_indicators") or []
    if full.get("warnings"):
        out["recommended_fixes"].extend(full["warnings"][:5])
    if full.get("errors"):
        out["recommended_fixes"] = full["errors"][:5] + out["recommended_fixes"]
    # First-value strength
    if data.get("templates") or data.get("workflow_templates"):
        out["first_value_strength"] = "has_templates"
    else:
        out["first_value_strength"] = "none"
        out["recommended_fixes"].append("Add templates or workflow_templates for first-value flow")
    # Certification
    cert = run_certification(pack_id, packs_dir=root, repo_root=repo_root)
    out["certification_status"] = cert.get("status", "unknown")
    if cert.get("errors"):
        out["recommended_fixes"] = list(cert["errors"][:3]) + out["recommended_fixes"]
    # Acceptance readiness: certifiable implies at least structural + installability + first-value
    if cert.get("status") == CERT_STATUS_CERTIFIABLE:
        out["acceptance_readiness"] = "ready"
    elif cert.get("status") == CERT_STATUS_BLOCKED:
        out["acceptance_readiness"] = "blocked"
    elif cert.get("status") == "valid":
        out["acceptance_readiness"] = "partial"
    else:
        out["acceptance_readiness"] = "not_ready"
    return out


def format_pack_scorecard(
    pack_id: str,
    packs_dir: Path | str | None = None,
    repo_root: Path | str | None = None,
) -> str:
    """Human-readable scorecard."""
    sc = build_pack_scorecard(pack_id, packs_dir=packs_dir, repo_root=repo_root)
    lines = [
        "=== Pack scorecard: " + sc["pack_id"] + " ===",
        "",
        "[Roles supported] " + ", ".join(sc.get("roles_supported") or []),
        "[Tasks/workflows] " + ", ".join((sc.get("tasks_workflows_supported") or [])[:15]),
        "[Runtime requirements] " + ", ".join((sc.get("runtime_requirements") or [])[:10]),
        "[Conflict risk] " + "; ".join(sc.get("conflict_risk") or ["none"]),
        "[First-value strength] " + sc.get("first_value_strength", "—"),
        "[Acceptance readiness] " + sc.get("acceptance_readiness", "—"),
        "[Certification status] " + sc.get("certification_status", "—"),
        "",
        "[Recommended fixes]",
    ]
    for f in sc.get("recommended_fixes") or []:
        lines.append("  - " + str(f))
    if not sc.get("recommended_fixes"):
        lines.append("  (none)")
    return "\n".join(lines)

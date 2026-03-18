"""
M24R: Install bundle — define installable local product bundle from current profile.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

from workflow_dataset.distribution.models import InstallBundle

BUNDLES_DIR = "data/local/distribution/bundles"


def _repo_root(root: Path | str | None) -> Path:
    if root is not None:
        return Path(root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def build_install_bundle(
    repo_root: Path | str | None = None,
    bundle_id: str | None = None,
) -> InstallBundle:
    """Build install bundle definition from current local deployment profile and readiness."""
    root = _repo_root(repo_root)
    if not bundle_id:
        bundle_id = "local_bundle"
    out = InstallBundle(
        bundle_id=bundle_id,
        version="1",
        description="Local installable product bundle (first-draft).",
        repo_root=str(root),
        generated_at=utc_now_iso(),
        required_capabilities=["config_exists", "edge_checks", "approval_registry_optional"],
        required_approvals_setup=["approval_registry_optional"],
        machine_assumptions={"local_only": True, "python_required": True},
    )
    try:
        from workflow_dataset.local_deployment.profile import build_local_deployment_profile
        profile = build_local_deployment_profile(repo_root=root)
        out.edge_profile_summary = profile.get("edge_profile") or {}
        out.readiness_summary = profile.get("readiness") or {}
        out.product_surfaces_summary = profile.get("product_surfaces") or {}
        if isinstance(out.edge_profile_summary, dict) and out.edge_profile_summary:
            out.machine_assumptions["tier"] = profile.get("tier")
    except Exception:
        pass
    return out


def write_install_bundle(
    bundle: InstallBundle,
    repo_root: Path | str | None = None,
) -> Path:
    """Write bundle definition to data/local/distribution/bundles/<bundle_id>.json."""
    root = _repo_root(repo_root)
    bundles_dir = root / BUNDLES_DIR
    bundles_dir.mkdir(parents=True, exist_ok=True)
    path = bundles_dir / f"{bundle.bundle_id}.json"
    data = {
        "bundle_id": bundle.bundle_id,
        "version": bundle.version,
        "description": bundle.description,
        "repo_root": bundle.repo_root,
        "generated_at": bundle.generated_at,
        "edge_profile_summary": bundle.edge_profile_summary,
        "readiness_summary": bundle.readiness_summary,
        "required_capabilities": bundle.required_capabilities,
        "required_approvals_setup": bundle.required_approvals_setup,
        "machine_assumptions": bundle.machine_assumptions,
        "product_surfaces_summary": bundle.product_surfaces_summary,
    }
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path

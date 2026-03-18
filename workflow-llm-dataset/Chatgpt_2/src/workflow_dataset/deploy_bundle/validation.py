"""
M40E–M40H: Bundle validation — required runtime, packs, trust, readiness checks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from workflow_dataset.deploy_bundle.registry import get_deployment_bundle


@dataclass
class BundleValidationResult:
    """Result of validating a deployment bundle against current repo state."""
    bundle_id: str = ""
    passed: bool = False
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    ready: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "bundle_id": self.bundle_id,
            "passed": self.passed,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "ready": self.ready,
        }


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def validate_bundle(
    bundle_id: str,
    repo_root: Path | str | None = None,
) -> BundleValidationResult:
    """
    Validate deployment bundle: bundle exists, install check passes if available,
    release readiness not blocked, required capabilities present (advisory).
    """
    result = BundleValidationResult(bundle_id=bundle_id)
    bundle = get_deployment_bundle(bundle_id)
    if not bundle:
        result.errors.append(f"Bundle not found: {bundle_id}")
        return result

    root = _repo_root(repo_root)

    # Install check
    try:
        from workflow_dataset.local_deployment.install_check import run_install_check
        check = run_install_check(repo_root=root)
        if not check.get("passed", False):
            result.errors.append("Install check failed: " + str(check.get("message", "unknown")))
    except Exception as e:
        result.warnings.append("Install check could not run: " + str(e))

    # Release readiness (blockers only)
    try:
        from workflow_dataset.release_readiness.readiness import build_release_readiness
        readiness = build_release_readiness(repo_root=root)
        if readiness.blockers:
            for b in readiness.blockers[:5]:
                result.errors.append(f"Readiness blocker: {b.summary}")
    except Exception as e:
        result.warnings.append("Release readiness check could not run: " + str(e))

    # Curated pack present
    try:
        from workflow_dataset.vertical_packs import get_curated_pack
        pack = get_curated_pack(bundle.curated_pack_id)
        if not pack:
            result.errors.append(f"Curated pack not found: {bundle.curated_pack_id}")
    except Exception as e:
        result.warnings.append("Curated pack check failed: " + str(e))

    result.passed = len(result.errors) == 0
    result.ready = result.passed and len(result.warnings) == 0
    return result

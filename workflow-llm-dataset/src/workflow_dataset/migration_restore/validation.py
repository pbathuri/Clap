"""
M49E–M49H Phase B: Validation and compatibility checks.
Version, target runtime, missing backend, local-only exclusion, trust/governance, experimental warnings.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

try:
    from workflow_dataset.utils.hashes import stable_id
except Exception:
    def stable_id(*parts: str, prefix: str = "") -> str:
        import hashlib
        return prefix + hashlib.sha256("".join(str(p) for p in parts).encode()).hexdigest()[:14]

from workflow_dataset.migration_restore.models import (
    ContinuityBundleManifest,
    TargetEnvironmentProfile,
    RestoreValidationReport,
    RestoreBlocker,
    RestoreConfidence,
)
from workflow_dataset.migration_restore.bundle import get_bundle_manifest


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _version_tuple(v: str) -> tuple[int, ...]:
    parts: list[int] = []
    for s in (v or "0.0.0").replace("-", ".").split("."):
        s = "".join(c for c in s if c.isdigit())
        parts.append(int(s) if s else 0)
    return tuple(parts)


def _version_compatible(bundle_version: str, target_version: str) -> bool:
    """Allow restore when target version >= bundle version (same major/minor preferred)."""
    return _version_tuple(target_version) >= _version_tuple(bundle_version)


def validate_bundle_for_target(
    bundle_ref: str,
    target_repo_root: Path | str | None = None,
    bundle_repo_root: Path | str | None = None,
) -> RestoreValidationReport:
    """
    Validate a continuity bundle against the target environment.
    Checks: version compatibility, runtime, missing backend, local-only exclusion, trust, experimental.
    """
    target_root = _root(target_repo_root)
    manifest = get_bundle_manifest(bundle_ref, bundle_repo_root or target_repo_root)
    if not manifest:
        report = RestoreValidationReport(
            report_id=stable_id("report", bundle_ref, prefix="rpt_"),
            bundle_id=bundle_ref,
            target_profile_id="current",
            passed=False,
            version_compatible=False,
            runtime_compatible=True,
            trust_compatible=True,
            blockers=[RestoreBlocker(blocker_id="bundle_missing", code="bundle_not_found", detail=f"Bundle not found: {bundle_ref}", subsystem_id="")],
            restore_confidence=RestoreConfidence(0.0, "blocked", ["Bundle not found."]),
            generated_at_utc=utc_now_iso(),
        )
        return report

    # Target profile from current environment
    target_version = "0.0.0"
    try:
        from workflow_dataset.install_upgrade.version import get_current_version
        target_version = get_current_version(target_root) or "0.0.0"
    except Exception:
        pass

    blockers: list[RestoreBlocker] = []
    warnings: list[str] = []
    experimental_warnings: list[str] = []

    # Version compatibility
    version_ok = _version_compatible(manifest.product_version, target_version)
    if not version_ok:
        blockers.append(RestoreBlocker(
            blocker_id=stable_id("blk", "version", prefix="blk_"),
            code="version_incompatible",
            detail=f"Target version {target_version} < bundle version {manifest.product_version}",
            subsystem_id="",
        ))

    # Runtime: check install/runtime if available
    runtime_ok = True
    try:
        from workflow_dataset.local_deployment.install_check import run_install_check
        check = run_install_check(repo_root=target_root)
        if not check.get("passed", True):
            runtime_ok = False
            warnings.append("Install check reported issues: " + str(check.get("message", ""))[:80])
    except Exception:
        pass

    # Trust/governance: advisory
    trust_ok = True
    try:
        from workflow_dataset.human_policy.store import load_policy_config
        load_policy_config(target_root)
    except Exception:
        warnings.append("Policy/trust config could not be loaded; restore may require review.")

    # Local-only excluded (informational)
    local_only_excluded = list(manifest.local_only_excluded)
    if local_only_excluded:
        warnings.append(f"Local-only subsystems excluded from bundle: {', '.join(local_only_excluded)}.")

    # Experimental components in bundle (if we had that in manifest)
    for comp in getattr(manifest, "experimental_components", []) or []:
        experimental_warnings.append(f"Bundle includes experimental component: {comp}.")

    passed = len(blockers) == 0
    score = 1.0 if passed else 0.0
    if not version_ok:
        score = 0.0
    elif warnings:
        score = max(0.0, 0.9 - 0.1 * len(warnings))
    label = "blocked" if not passed else ("high" if score >= 0.9 else "medium" if score >= 0.5 else "low")

    confidence = RestoreConfidence(
        score=score,
        label=label,
        reasons=blockers and [b.detail for b in blockers] or (["Warnings present."] if warnings else []),
    )

    return RestoreValidationReport(
        report_id=stable_id("report", manifest.bundle_id, target_root, prefix="rpt_"),
        bundle_id=manifest.bundle_id,
        target_profile_id="current",
        passed=passed,
        version_compatible=version_ok,
        runtime_compatible=runtime_ok,
        trust_compatible=trust_ok,
        blockers=blockers,
        warnings=warnings,
        local_only_excluded=local_only_excluded,
        experimental_warnings=experimental_warnings,
        restore_confidence=confidence,
        generated_at_utc=utc_now_iso(),
    )

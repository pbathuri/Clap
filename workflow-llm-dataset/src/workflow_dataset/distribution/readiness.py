"""
M24R–M24U: Deploy readiness — aggregate install check + package readiness + rollout readiness summary.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def _repo_root(root: Path | str | None) -> Path:
    if root is not None:
        return Path(root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def build_deploy_readiness(repo_root: Path | str | None = None) -> dict[str, Any]:
    """Aggregate deploy readiness: install_check, package_readiness, rollout readiness (demo/first-user)."""
    root = _repo_root(repo_root)
    out: dict[str, Any] = {
        "install_check_passed": False,
        "package_ready_for_first_user": False,
        "rollout_demo_ready": False,
        "rollout_first_user_ready": False,
        "summary": "",
    }
    try:
        from workflow_dataset.local_deployment.install_check import run_install_check
        check = run_install_check(repo_root=root)
        out["install_check_passed"] = check.get("passed", False)
    except Exception:
        pass
    try:
        from workflow_dataset.package_readiness.summary import build_readiness_summary
        ready = build_readiness_summary(root)
        out["package_ready_for_first_user"] = ready.get("ready_for_first_real_user_install", False)
    except Exception:
        pass
    try:
        from workflow_dataset.rollout.readiness import build_rollout_readiness_report
        r = build_rollout_readiness_report(root)
        out["rollout_demo_ready"] = r.get("demo_ready", False)
        out["rollout_first_user_ready"] = r.get("first_user_ready", False)
    except Exception:
        pass
    parts = []
    if out["install_check_passed"]:
        parts.append("install_check=pass")
    else:
        parts.append("install_check=fail")
    if out["package_ready_for_first_user"]:
        parts.append("first_user_install=ready")
    else:
        parts.append("first_user_install=not_ready")
    if out["rollout_demo_ready"]:
        parts.append("demo_ready=yes")
    else:
        parts.append("demo_ready=no")
    out["summary"] = "  ".join(parts)
    return out


def format_deploy_readiness(repo_root: Path | str | None = None) -> str:
    """One-block deploy readiness report."""
    r = build_deploy_readiness(repo_root)
    lines = [
        "=== Deploy readiness ===",
        "",
        f"Install check passed: {r.get('install_check_passed')}",
        f"Package ready for first user install: {r.get('package_ready_for_first_user')}",
        f"Rollout demo-ready: {r.get('rollout_demo_ready')}",
        f"Rollout first-user-ready: {r.get('rollout_first_user_ready')}",
        "",
        f"Summary: {r.get('summary', '')}",
        "",
        "See: workflow-dataset package install-check | package readiness-report | rollout readiness",
    ]
    return "\n".join(lines)

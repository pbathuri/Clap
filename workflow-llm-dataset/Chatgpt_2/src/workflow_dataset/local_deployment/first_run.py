"""
M23R: First-run install/bootstrap flow. Ensures dirs, runs install-check, runs onboarding, hands off to first-run summary.
Local-only; no hidden services.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.local_deployment.profile import get_deployment_dir
from workflow_dataset.local_deployment.install_check import run_install_check, format_install_check_report


def _repo_root(root: Path | str | None) -> Path:
    if root is not None:
        return Path(root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _ensure_local_dirs(root: Path) -> list[str]:
    """Ensure core data/local dirs exist. Returns list of created paths (for reporting)."""
    from workflow_dataset.edge.profile import SANDBOX_PATHS
    created: list[str] = []
    for rel in SANDBOX_PATHS:
        p = root / rel
        if not p.exists():
            p.mkdir(parents=True, exist_ok=True)
            created.append(rel)
    deploy_dir = get_deployment_dir(root)
    if not deploy_dir.exists():
        deploy_dir.mkdir(parents=True, exist_ok=True)
        created.append(deploy_dir.relative_to(root).as_posix())
    return created


def run_first_run(
    repo_root: Path | str | None = None,
    config_path: str = "configs/settings.yaml",
    skip_onboarding: bool = False,
) -> dict[str, Any]:
    """
    First-run flow: ensure dirs, run install-check, run onboarding bootstrap (unless skipped),
    build first-run summary. Handoff into onboarding. No cloud; no hidden services.
    Returns: install_check_passed, created_dirs, onboarding_status, first_run_summary, report_text.
    """
    root = _repo_root(repo_root)
    out: dict[str, Any] = {
        "install_check_passed": False,
        "created_dirs": [],
        "onboarding_status": None,
        "first_run_summary": None,
        "report_text": "",
        "errors": [],
    }

    # 1. Ensure local dirs
    try:
        out["created_dirs"] = _ensure_local_dirs(root)
    except Exception as e:
        out["errors"].append(f"ensure_dirs: {e}")

    # 2. Install check
    try:
        check = run_install_check(repo_root=root, config_path=config_path)
        out["install_check_passed"] = check.get("passed", False)
        out["install_check_result"] = check
    except Exception as e:
        out["errors"].append(f"install_check: {e}")

    # 3. Onboarding bootstrap (persist profile)
    if not skip_onboarding:
        try:
            from workflow_dataset.onboarding.onboarding_flow import run_onboarding_flow
            out["onboarding_status"] = run_onboarding_flow(
                repo_root=root, config_path=config_path, persist_profile=True
            )
        except Exception as e:
            out["errors"].append(f"onboarding: {e}")

    # 4. First-run summary (for handoff)
    try:
        from workflow_dataset.onboarding.product_summary import build_first_run_summary, format_first_run_summary
        out["first_run_summary"] = build_first_run_summary(repo_root=root, config_path=config_path)
        out["report_text"] = format_install_check_report(out.get("install_check_result") or {})
        out["report_text"] += "\n\n"
        out["report_text"] += format_first_run_summary(summary=out["first_run_summary"])
    except Exception as e:
        out["errors"].append(f"first_run_summary: {e}")
        if not out["report_text"]:
            out["report_text"] = format_install_check_report(out.get("install_check_result") or {})

    return out

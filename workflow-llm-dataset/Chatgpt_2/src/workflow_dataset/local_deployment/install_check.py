"""
M23R: Install-time readiness validation. Local-only; no mutation beyond reporting.
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


def run_install_check(
    repo_root: Path | str | None = None,
    config_path: str = "configs/settings.yaml",
) -> dict[str, Any]:
    """
    Validate local runtime requirements at install time. Read-only.
    Returns: passed, failed_required, missing_prereqs, checks (list), summary (for report).
    """
    root = _repo_root(repo_root)
    out: dict[str, Any] = {
        "passed": False,
        "failed_required": 0,
        "missing_prereqs": [],
        "checks": [],
        "summary": "",
        "product_readiness": {},
        "errors": [],
    }

    # Edge readiness checks
    try:
        from workflow_dataset.edge.checks import run_readiness_checks, checks_summary
        checks = run_readiness_checks(repo_root=root, config_path=config_path)
        summary = checks_summary(checks)
        out["checks"] = [
            {"check_id": c.get("check_id"), "passed": c.get("passed"), "message": c.get("message"), "optional": c.get("optional")}
            for c in checks
        ]
        out["failed_required"] = summary.get("failed_required", 0)
        out["passed"] = summary.get("ready", False)
        failed_req = [c for c in checks if not c.get("passed") and not c.get("optional")]
        out["missing_prereqs"] = [c.get("message", c.get("check_id", "")) for c in failed_req]
    except Exception as e:
        out["errors"].append(f"edge_checks: {e}")
        out["passed"] = False

    # Package readiness (product side)
    try:
        from workflow_dataset.package_readiness.summary import build_readiness_summary
        ready = build_readiness_summary(repo_root=root)
        out["product_readiness"] = {
            "ready_for_first_real_user_install": ready.get("ready_for_first_real_user_install"),
            "missing_runtime_prerequisites": ready.get("missing_runtime_prerequisites", []),
        }
        if ready.get("missing_runtime_prerequisites") and not out["missing_prereqs"]:
            out["missing_prereqs"] = list(ready.get("missing_runtime_prerequisites", []))
    except Exception as e:
        out["errors"].append(f"readiness: {e}")

    # Summary line
    if out["passed"] and not out["missing_prereqs"]:
        out["summary"] = "All required checks passed. Ready for local install."
    elif out["failed_required"]:
        out["summary"] = f"{out['failed_required']} required check(s) failed. Fix missing prerequisites before install."
    else:
        out["summary"] = "Some checks failed. Review missing_prereqs and optional checks."
    return out


def format_install_check_report(result: dict[str, Any]) -> str:
    """Human-readable install-check report."""
    lines = [
        "=== Install check (local deployment) ===",
        "",
        result.get("summary", ""),
        "",
    ]
    if result.get("missing_prereqs"):
        lines.append("[Missing prerequisites]")
        for m in result["missing_prereqs"]:
            lines.append(f"  - {m}")
        lines.append("")
    lines.append("[Checks]")
    for c in result.get("checks") or []:
        status = "PASS" if c.get("passed") else "FAIL"
        opt = " (optional)" if c.get("optional") else ""
        lines.append(f"  {status}{opt}  {c.get('check_id', '')} — {c.get('message', '')}")
    if result.get("errors"):
        lines.append("")
        lines.append("[Errors]")
        for e in result["errors"]:
            lines.append(f"  - {e}")
    lines.append("")
    lines.append("(Validation only. No changes made.)")
    return "\n".join(lines)

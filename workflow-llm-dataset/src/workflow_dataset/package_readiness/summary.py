"""
M23V: Build package/install readiness summary from edge checks, release, and trust.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def _repo_root(root: Path | str | None) -> Path:
    if root is not None:
        return Path(root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root())
    except Exception:
        return Path.cwd()


def build_readiness_summary(repo_root: Path | str | None = None) -> dict[str, Any]:
    """
    Build readiness summary: current_machine_readiness, product_readiness,
    missing_runtime_prerequisites, ready_for_first_real_user_install, experimental.
    No installer rewrite; report only.
    """
    root = _repo_root(repo_root)
    out: dict[str, Any] = {
        "current_machine_readiness": {},
        "product_readiness": {},
        "missing_runtime_prerequisites": [],
        "ready_for_first_real_user_install": False,
        "ready_reasons": [],
        "not_ready_reasons": [],
        "experimental": [],
        "errors": [],
    }

    # Machine readiness (edge checks)
    try:
        from workflow_dataset.edge.checks import run_readiness_checks, checks_summary
        checks = run_readiness_checks(repo_root=root)
        summary = checks_summary(checks)
        out["current_machine_readiness"] = {
            "ready": summary.get("ready", False),
            "passed": summary.get("passed", 0),
            "total": len(checks),
            "failed_required": summary.get("failed_required", 0),
            "optional_disabled": summary.get("optional_disabled", 0),
        }
        failed_required = [c for c in checks if not c.get("passed") and not c.get("optional")]
        out["missing_runtime_prerequisites"] = [c.get("message", c.get("check_id", "")) for c in failed_required]
    except Exception as e:
        out["errors"].append(f"edge_checks: {e}")

    # Product readiness (release report, staging, review state)
    try:
        from workflow_dataset.release.dashboard_data import get_dashboard_data
        from workflow_dataset.release.staging_board import load_staging_board
        dash = get_dashboard_data(repo_root=root)
        board = load_staging_board(repo_root=root)
        release_report = root / "data/local/release/release_readiness_report.md"
        rp = dash.get("review_package") or {}
        staging = dash.get("staging") or {}
        staged_count = staging.get("staged_count", 0) or len((board.get("items") or []))
        out["product_readiness"] = {
            "release_readiness_report_exists": release_report.exists(),
            "unreviewed_count": rp.get("unreviewed_count", 0),
            "package_pending_count": rp.get("package_pending_count", 0),
            "staged_count": staged_count,
        }
    except Exception as e:
        out["errors"].append(f"product: {e}")

    # Ready for first real-user install?
    machine = out.get("current_machine_readiness") or {}
    product = out.get("product_readiness") or {}
    if machine.get("ready"):
        out["ready_reasons"].append("Machine readiness checks passed.")
    else:
        out["not_ready_reasons"].append("One or more required machine checks failed.")
    if out.get("missing_runtime_prerequisites"):
        for m in out["missing_runtime_prerequisites"][:5]:
            out["not_ready_reasons"].append(f"Missing: {m}")
    if product.get("release_readiness_report_exists"):
        out["ready_reasons"].append("Release readiness report present.")
    else:
        out["not_ready_reasons"].append("Release readiness report missing (run: workflow-dataset release report).")

    out["ready_for_first_real_user_install"] = (
        machine.get("ready", False)
        and len(out["not_ready_reasons"]) == 0
    )

    # Experimental: areas not yet production-ready (advisory list)
    try:
        from workflow_dataset.desktop_bench.board import board_report
        br = board_report(limit_runs=3, root=root)
        if br.get("latest_trust_status") and br["latest_trust_status"] not in ("trusted", "usable_with_simulation_only"):
            out["experimental"].append("Desktop benchmark: " + str(br.get("latest_trust_status")))
    except Exception:
        pass
    out["experimental"].append("Macros/routines: run in simulate first; real mode requires approvals.")
    out["experimental"].append("Corrections and propose-updates: operator review required before apply.")

    return out

"""
M23W: Integrated validation report — health + test run summary, categorized failures. No auto-fix.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.validation.env_health import check_environment_health
from workflow_dataset.validation.run_validation import run_pytest_and_categorize


def build_validation_report(repo_root: Path | str | None = None) -> dict[str, Any]:
    """Build combined health + test run report. Does not run pytest if health required_ok is False (optional)."""
    root = Path(repo_root) if repo_root else None
    try:
        from workflow_dataset.path_utils import get_repo_root
        root = get_repo_root() if not repo_root else Path(repo_root)
    except Exception:
        root = root or Path.cwd()
    health = check_environment_health(root)
    test_run = run_pytest_and_categorize(root)
    return {
        "environment_health": health,
        "test_run": test_run,
        "ready_for_operator_expansion": health.get("required_ok", False) and test_run.get("ran") and test_run.get("failed", 0) == 0 and test_run.get("errors", 0) == 0,
    }


def format_validation_report_md(report: dict[str, Any] | None = None, repo_root: Path | str | None = None) -> str:
    """Format validation report as markdown."""
    if report is None:
        report = build_validation_report(repo_root)
    lines = [
        "# Integrated validation report (M23W)",
        "",
        "## Environment health",
        f"- required_ok: {report.get('environment_health', {}).get('required_ok')}",
        f"- optional_ok: {report.get('environment_health', {}).get('optional_ok')}",
        f"- incubator_present: {report.get('environment_health', {}).get('incubator_present')}",
        f"- python_version: {report.get('environment_health', {}).get('python_version')}",
        "",
        "## Test run",
        f"- ran: {report.get('test_run', {}).get('ran')}",
        f"- passed: {report.get('test_run', {}).get('passed', 0)}",
        f"- failed: {report.get('test_run', {}).get('failed', 0)}",
        f"- errors: {report.get('test_run', {}).get('errors', 0)}",
        f"- skipped: {report.get('test_run', {}).get('skipped', 0)}",
        "",
        "## Failure categories",
    ]
    for cat, items in (report.get("test_run") or {}).get("categories", {}).items():
        lines.append(f"- **{cat}**: {len(items)}")
        for item in items[:5]:
            lines.append(f"  - {item[:100]}")
    lines.extend([
        "",
        "## Ready for operator-facing expansion",
        str(report.get("ready_for_operator_expansion", False)),
        "",
    ])
    return "\n".join(lines)

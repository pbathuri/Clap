"""
M23V: Format package/install readiness report.
"""

from __future__ import annotations

from typing import Any

from workflow_dataset.package_readiness.summary import build_readiness_summary


def format_readiness_report(summary: dict[str, Any] | None = None, repo_root=None) -> str:
    """Produce human-readable package/install readiness report."""
    if summary is None:
        summary = build_readiness_summary(repo_root)
    lines = [
        "=== Package / install readiness report ===",
        "",
    ]
    if summary.get("errors"):
        lines.append("[Errors] " + "; ".join(summary["errors"][:5]))
        lines.append("")

    mr = summary.get("current_machine_readiness") or {}
    lines.append("[Current machine readiness]")
    lines.append(f"  ready: {mr.get('ready')}  passed: {mr.get('passed')}/{mr.get('total', 0)}  failed_required: {mr.get('failed_required', 0)}  optional_disabled: {mr.get('optional_disabled', 0)}")
    lines.append("")

    pr = summary.get("product_readiness") or {}
    lines.append("[Current product readiness]")
    lines.append(f"  release_readiness_report: {'present' if pr.get('release_readiness_report_exists') else 'missing'}")
    lines.append(f"  unreviewed workspaces: {pr.get('unreviewed_count', 0)}  package_pending: {pr.get('package_pending_count', 0)}  staged: {pr.get('staged_count', 0)}")
    lines.append("")

    miss = summary.get("missing_runtime_prerequisites") or []
    if miss:
        lines.append("[Missing runtime/integration prerequisites]")
        for m in miss:
            lines.append(f"  - {m}")
        lines.append("")

    lines.append("--- First real-user install ---")
    lines.append(f"  ready: {summary.get('ready_for_first_real_user_install')}")
    for r in summary.get("ready_reasons", []):
        lines.append(f"  + {r}")
    for r in summary.get("not_ready_reasons", []):
        lines.append(f"  - {r}")
    lines.append("")

    exp = summary.get("experimental") or []
    if exp:
        lines.append("[What remains experimental]")
        for e in exp:
            lines.append(f"  - {e}")
        lines.append("")
    lines.append("(No installer changes. Report only.)")
    return "\n".join(lines)

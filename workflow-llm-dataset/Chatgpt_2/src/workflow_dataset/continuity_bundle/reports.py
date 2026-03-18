"""
M49D.1: Operator-facing portability reports — portable, review-required, excluded, rebuild-only.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.continuity_bundle.portability import get_portability_boundaries
from workflow_dataset.continuity_bundle.sensitivity_policies import (
    get_sensitivity_policy,
    apply_policy_to_boundaries,
    POLICY_TRANSFER_WITH_REVIEW,
)
from workflow_dataset.continuity_bundle.components import get_component
from workflow_dataset.continuity_bundle.profiles import get_profile


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def get_portability_report(
    repo_root: Path | str | None = None,
    profile_id: str | None = None,
    sensitivity_policy_id: str | None = None,
) -> dict[str, Any]:
    """
    Operator-facing report: what is portable, review-required, excluded, rebuild-only.
    Optionally filtered by bundle profile and/or sensitivity policy.
    """
    root = _root(repo_root)
    boundaries = get_portability_boundaries(root)
    policy = get_sensitivity_policy(sensitivity_policy_id or POLICY_TRANSFER_WITH_REVIEW)
    if policy is None:
        policy = get_sensitivity_policy(POLICY_TRANSFER_WITH_REVIEW)
    applied = apply_policy_to_boundaries(boundaries, policy) if policy else {}

    # Enrich with component labels for operator readability
    def label_list(component_ids: list[str]) -> list[dict[str, Any]]:
        out = []
        for cid in component_ids:
            c = get_component(cid, root)
            out.append({
                "component_id": cid,
                "label": c.label if c else cid.replace("_", " ").title(),
                "sensitive": c.sensitive if c else False,
                "review_required": c.review_required if c else False,
            })
        return out

    report: dict[str, Any] = {
        "portable": applied.get("portable", []),
        "portable_count": applied.get("portable_count", 0),
        "portable_detail": label_list(applied.get("portable", [])),
        "review_required": applied.get("review_required", []),
        "review_required_count": applied.get("review_required_count", 0),
        "review_required_detail": label_list(applied.get("review_required", [])),
        "excluded": applied.get("excluded", []),
        "excluded_count": applied.get("excluded_count", 0),
        "excluded_detail": label_list(applied.get("excluded", [])),
        "rebuild_only": applied.get("rebuild_only", []),
        "rebuild_only_count": applied.get("rebuild_only_count", 0),
        "rebuild_only_detail": label_list(applied.get("rebuild_only", [])),
        "summary": applied.get("summary", ""),
        "sensitivity_policy_id": applied.get("policy_id", sensitivity_policy_id or POLICY_TRANSFER_WITH_REVIEW),
        "sensitivity_policy_label": applied.get("policy_label", ""),
    }
    if profile_id:
        profile = get_profile(profile_id)
        report["profile_id"] = profile_id
        report["profile_label"] = profile.label if profile else profile_id
        report["profile_description"] = profile.description if profile else ""
    return report


def format_portability_report_text(
    report: dict[str, Any],
    max_items: int = 15,
) -> str:
    """Format portability report as operator-facing text lines."""
    lines: list[str] = []
    lines.append("--- Portability report ---")
    lines.append(f"Policy: {report.get('sensitivity_policy_label', report.get('sensitivity_policy_id', '—'))}")
    if report.get("profile_id"):
        lines.append(f"Profile: {report.get('profile_label', report['profile_id'])}")
    lines.append(f"Summary: {report.get('summary', '')}")
    lines.append("")
    lines.append(f"Portable ({report.get('portable_count', 0)}):")
    for d in report.get("portable_detail", [])[:max_items]:
        lines.append(f"  • {d.get('label', d.get('component_id', ''))} ({d.get('component_id', '')})")
    if report.get("portable_count", 0) > max_items:
        lines.append(f"  ... and {report['portable_count'] - max_items} more")
    lines.append("")
    lines.append(f"Review required ({report.get('review_required_count', 0)}):")
    for d in report.get("review_required_detail", [])[:max_items]:
        lines.append(f"  • {d.get('label', d.get('component_id', ''))} [review]")
    if report.get("review_required_count", 0) > max_items:
        lines.append(f"  ... and {report['review_required_count'] - max_items} more")
    lines.append("")
    lines.append(f"Excluded ({report.get('excluded_count', 0)}):")
    for d in report.get("excluded_detail", [])[:max_items]:
        lines.append(f"  • {d.get('label', d.get('component_id', ''))} [excluded]")
    if report.get("excluded_count", 0) > max_items:
        lines.append(f"  ... and {report['excluded_count'] - max_items} more")
    lines.append("")
    lines.append(f"Rebuild only ({report.get('rebuild_only_count', 0)}):")
    for d in report.get("rebuild_only_detail", [])[:max_items]:
        lines.append(f"  • {d.get('label', d.get('component_id', ''))} [rebuild on restore]")
    if report.get("rebuild_only_count", 0) > max_items:
        lines.append(f"  ... and {report['rebuild_only_count'] - max_items} more")
    return "\n".join(lines)

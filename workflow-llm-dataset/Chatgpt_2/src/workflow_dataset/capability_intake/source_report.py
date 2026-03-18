"""
M21: Generate a readable source intake report. Local file output.
"""

from __future__ import annotations

from pathlib import Path

from workflow_dataset.capability_intake.source_registry import list_sources


def write_source_report(
    output_path: Path | str | None = None,
    registry_path: Path | str | None = None,
) -> Path:
    """Write a markdown report of all registered sources with roles and recommendations."""
    out = Path(output_path) if output_path else Path("data/local/capability_intake/source_report.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    sources = list_sources(registry_path)
    lines = [
        "# Capability intake source report",
        "",
        f"**Total sources:** {len(sources)}",
        "",
        "## By adoption recommendation",
        "",
    ]
    by_adoption: dict[str, list] = {}
    for s in sources:
        by_adoption.setdefault(s.adoption_recommendation or "unknown", []).append(s)
    for rec in sorted(by_adoption.keys()):
        lines.append(f"### {rec}")
        lines.append("")
        for s in by_adoption[rec]:
            lines.append(f"- **{s.source_id}** — {s.name}")
            lines.append(f"  - Role: {s.recommended_role} | Risk: {s.safety_risk_level} | Local fit: {s.local_runtime_fit}")
            if s.canonical_url:
                lines.append(f"  - URL: {s.canonical_url}")
            if s.unresolved_reason:
                lines.append(f"  - Unresolved: {s.unresolved_reason}")
            lines.append("")
        lines.append("")
    lines.append("## Full entries")
    lines.append("")
    for s in sources:
        lines.append(f"### {s.source_id}")
        lines.append("")
        lines.append(f"- **Name:** {s.name}")
        lines.append(f"- **Type:** {s.source_type} | **Kind:** {s.source_kind}")
        lines.append(f"- **URL:** {s.canonical_url or '(none)'}")
        lines.append(f"- **Description:** {s.description[:200] if s.description else '(none)'}")
        lines.append(f"- **License:** {s.license or '(unknown)'}")
        lines.append(f"- **Role:** {s.recommended_role} | **Risk:** {s.safety_risk_level}")
        lines.append(f"- **Local fit:** {s.local_runtime_fit} | **Cloud pack fit:** {s.cloud_pack_fit}")
        lines.append(f"- **Adoption:** {s.adoption_recommendation}")
        if s.unresolved_reason:
            lines.append(f"- **Unresolved:** {s.unresolved_reason}")
        if s.notes:
            lines.append(f"- **Notes:** {s.notes[:300]}")
        lines.append("")
    out.write_text("\n".join(lines), encoding="utf-8")
    return out

"""
Build the setup onboarding summary report from session and progress.

Produces a concise local markdown summary of what the agent has learned.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.setup.setup_models import SetupSession, SetupProgress, SetupStage


def build_summary_markdown(
    session: SetupSession,
    progress: SetupProgress,
    *,
    report_path: Path | str | None = None,
) -> str:
    """
    Build markdown summary. If report_path is set, write file and return path as first line.
    """
    lines = [
        "# Setup onboarding summary",
        "",
        f"Session: {session.session_id}",
        f"Onboarding mode: {session.onboarding_mode}",
        f"Updated: {progress.updated_utc}",
        "",
        "## Progress",
        f"- Files scanned: {progress.files_scanned}",
        f"- Artifacts classified: {progress.artifacts_classified}",
        f"- Docs parsed: {progress.docs_parsed}",
        f"- Projects detected: {progress.projects_detected}",
        f"- Style signatures extracted: {progress.style_patterns_extracted}",
        f"- Graph nodes created: {progress.graph_nodes_created}",
        f"- Adapter errors: {progress.adapter_errors} skips: {progress.adapter_skips}",
        "",
        "## Discovered domains",
    ]
    for d in session.config_snapshot.get("discovered_domains", []):
        if isinstance(d, dict):
            lines.append(f"- {d.get('domain_id', '')}: {d.get('label', '')} (confidence {d.get('confidence', 0)})")
        else:
            lines.append(f"- {getattr(d, 'domain_id', '')}: {getattr(d, 'label', '')}")
    by_family = progress.details.get("by_family") if progress.details else None
    if by_family and isinstance(by_family, dict):
        lines.append("## Artifact families")
        for fam, count in sorted(by_family.items(), key=lambda x: (-x[1], x[0]))[:25]:
            lines.append(f"- {fam}: {count}")
        lines.append("")
    elif by_family and isinstance(by_family, list):
        lines.append("## Artifact families")
        for x in by_family[:25]:
            lines.append(f"- {x}")
        lines.append("")
    if progress.details:
        lines.append("## Details")
        for k, v in progress.details.items():
            if k == "by_family":
                continue
            if k in ("domains",) and isinstance(v, list):
                lines.append(f"- {k}: {', '.join(str(x) for x in v[:15])}{'...' if len(v) > 15 else ''}")
            elif isinstance(v, (list, dict)) and len(str(v)) > 200:
                lines.append(f"- {k}: (see session details)")
            else:
                lines.append(f"- {k}: {v}")
        lines.append("")
    lines.append("## Notes")
    lines.append("Learning is local-only. Use setup-status for live progress.")
    if session.onboarding_mode == "full_onboarding":
        lines.append("Full onboarding: raw text parsing was allowed for supported documents.")
    text = "\n".join(lines)
    if report_path:
        path = Path(report_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return text

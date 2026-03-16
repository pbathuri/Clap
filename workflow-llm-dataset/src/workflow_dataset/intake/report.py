"""
M22D: Intake report — file inventory, parse summary, likely workflow associations. Local-only.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.intake.registry import INTAKE_ROOT, get_intake


def _repo_root(root: Path | str | None) -> Path:
    if root is not None:
        return Path(root)
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root())
    except Exception:
        return Path.cwd()


def intake_report(
    label: str,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Build intake report for a label: file inventory, parse summary (counts by extension),
    and suggested workflows. Does not mutate anything.
    """
    root = _repo_root(repo_root)
    entry = get_intake(label, repo_root=root)
    if not entry:
        return {"error": f"Intake set not found: {label}", "label": label}
    sp = entry.get("snapshot_path")
    if sp:
        snap_dir = Path(sp)
    else:
        snap_rel = entry.get("snapshot_dir")
        snap_dir = root / INTAKE_ROOT / snap_rel if snap_rel else root / INTAKE_ROOT / (entry.get("label") or "")
    out: dict[str, Any] = {
        "label": entry.get("label"),
        "input_type": entry.get("input_type", "mixed"),
        "created_at": entry.get("created_at"),
        "source_paths": entry.get("source_paths", []),
        "snapshot_dir": entry.get("snapshot_dir"),
        "file_inventory": [],
        "parse_summary": {"by_extension": {}, "total_files": 0, "total_chars": 0},
        "suggested_workflows": [],
    }
    if not snap_dir.exists() or not snap_dir.is_dir():
        out["file_inventory"] = entry.get("files", [])[:50]
        out["parse_summary"]["total_files"] = entry.get("file_count", 0)
        return out
    by_ext: dict[str, int] = {}
    total_chars = 0
    inventory: list[dict[str, Any]] = []
    for f in sorted(snap_dir.rglob("*")):
        if not f.is_file():
            continue
        ext = f.suffix.lower() or "(no ext)"
        by_ext[ext] = by_ext.get(ext, 0) + 1
        try:
            total_chars += len(f.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            pass
        try:
            rel = f.relative_to(snap_dir)
        except ValueError:
            rel = f.name
        inventory.append({"path": str(rel), "extension": ext})
    out["file_inventory"] = inventory[:100]
    out["parse_summary"]["by_extension"] = by_ext
    out["parse_summary"]["total_files"] = len(inventory)
    out["parse_summary"]["total_chars"] = total_chars
    # Suggest workflows from content type
    if by_ext.get(".md") or by_ext.get(".txt"):
        out["suggested_workflows"].append("ops_reporting_workspace")
        out["suggested_workflows"].append("weekly_status")
    if by_ext.get(".csv") or by_ext.get(".json"):
        out["suggested_workflows"].append("ops_reporting_workspace")
    if "meeting" in (entry.get("input_type") or "").lower() or "meeting" in (label or "").lower():
        out["suggested_workflows"].append("meeting_brief_bundle")
    if not out["suggested_workflows"]:
        out["suggested_workflows"] = ["ops_reporting_workspace", "weekly_status"]
    return out


def format_intake_report_text(report: dict[str, Any]) -> str:
    """Format intake report as human-readable text."""
    if report.get("error"):
        return f"Error: {report['error']}"
    lines: list[str] = []
    lines.append(f"# Intake: {report.get('label', '—')}")
    lines.append("")
    lines.append(f"- **Input type:** {report.get('input_type', '—')}")
    lines.append(f"- **Created:** {report.get('created_at', '—')}")
    lines.append(f"- **Snapshot:** {report.get('snapshot_dir', '—')}")
    lines.append("")
    lines.append("## Source paths")
    for p in report.get("source_paths", []):
        lines.append(f"  - {p}")
    lines.append("")
    ps = report.get("parse_summary", {})
    lines.append("## Parse summary")
    lines.append(f"  - Total files: {ps.get('total_files', 0)}")
    lines.append(f"  - Total chars: {ps.get('total_chars', 0)}")
    for ext, count in sorted((ps.get("by_extension") or {}).items()):
        lines.append(f"  - {ext}: {count}")
    lines.append("")
    lines.append("## Suggested workflows")
    for w in report.get("suggested_workflows", []):
        lines.append(f"  - {w}")
    lines.append("")
    lines.append("## File inventory (sample)")
    for it in (report.get("file_inventory") or [])[:30]:
        lines.append(f"  - {it.get('path', it)}")
    return "\n".join(lines)

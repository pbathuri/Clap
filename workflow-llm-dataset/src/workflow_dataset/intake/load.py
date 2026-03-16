"""
M22D: Load intake set content for workflow grounding. Reads from snapshot only; local-only.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

MAX_INTAKE_CONTENT_CHARS = 8000


def _repo_root(root: Path | str | None) -> Path:
    if root is not None:
        return Path(root)
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root())
    except Exception:
        return Path.cwd()


def load_intake_content(
    label: str,
    repo_root: Path | str | None = None,
    max_content_chars: int = MAX_INTAKE_CONTENT_CHARS,
) -> tuple[str, list[dict[str, Any]]]:
    """
    Load a registered intake set by label. Reads from its snapshot dir.
    Returns (combined_content, source_descriptions) for use in release demo task_context.
    source_descriptions: list of {"type": "intake", "path_or_name": label, "path": str, "rel_path": str}.
    """
    from workflow_dataset.intake.registry import get_intake
    root = _repo_root(repo_root)
    entry = get_intake(label, repo_root=root)
    if not entry:
        return "", []
    from workflow_dataset.intake.registry import INTAKE_ROOT
    snapshot_path = entry.get("snapshot_path")
    if snapshot_path:
        snap_dir = Path(snapshot_path)
    else:
        snap_rel = entry.get("snapshot_dir")
        snap_dir = root / INTAKE_ROOT / snap_rel if snap_rel else root / INTAKE_ROOT / (entry.get("label") or "")
    if not snap_dir.exists() or not snap_dir.is_dir():
        return "", []
    parts: list[str] = []
    source_descriptions: list[dict[str, Any]] = []
    for f in sorted(snap_dir.rglob("*")):
        if not f.is_file():
            continue
        if f.suffix.lower() not in (".md", ".txt", ".csv", ".json", ".yaml", ".yml"):
            continue
        try:
            text = f.read_text(encoding="utf-8", errors="replace").strip()
        except Exception:
            continue
        if not text:
            continue
        try:
            rel = f.relative_to(snap_dir)
        except ValueError:
            rel = f.name
        parts.append(f"--- {rel} ---\n{text}")
        source_descriptions.append({
            "type": "intake",
            "path_or_name": label,
            "path": str(f),
            "rel_path": str(rel),
        })
    combined = "\n\n".join(parts)
    if len(combined) > max_content_chars:
        combined = combined[:max_content_chars] + "\n[... truncated]"
    return combined, source_descriptions

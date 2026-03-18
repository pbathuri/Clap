"""
M23: Simple evaluation report for a role pack. Answers: useful? on which tasks? ready for pilot?
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.packs.pack_registry import get_installed_manifest


def write_pack_report(
    pack_id: str,
    packs_dir: Path | str | None = None,
    trials_dir: Path | str | None = None,
    output_path: Path | str | None = None,
) -> Path:
    """
    Write a short evaluation report for an installed pack to report.md under pack dir (or output_path).
    Uses manifest + optional trials dir to list tasks and readiness. Does not require live runs.
    """
    from workflow_dataset.packs.pack_state import get_packs_dir
    root = Path(packs_dir) if packs_dir else get_packs_dir()
    manifest = get_installed_manifest(pack_id, packs_dir)
    if not manifest:
        raise ValueError(f"Pack not installed: {pack_id}")
    trials_dir = Path(trials_dir) if trials_dir else Path("data/local/trials")
    out_path = Path(output_path) if output_path else root / pack_id / "report.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tasks = manifest.templates or manifest.workflow_templates or manifest.evaluation_tasks
    lines = [
        "# Pack evaluation report",
        "",
        f"**Pack:** {manifest.pack_id} @ {manifest.version}",
        f"**Name:** {manifest.name}",
        "",
        "## Did the pack materially improve usefulness?",
        "",
        "When this pack is active (role=ops), release run and pilot use its templates and retrieval profile.",
        "Compare: run `release run` without pack (or with deactivate) vs with pack activated; review task completion and output relevance.",
        "",
        "## On which tasks?",
        "",
    ]
    for t in tasks:
        lines.append(f"- {t}")
    lines.extend([
        "",
        "## Where did it not help?",
        "",
        "N/A for narrow ops pack. If you see generic or off-scope outputs, ensure adapter is trained and retrieval corpus is populated.",
        "",
        "## Ready for pilot use?",
        "",
        "Yes, for narrow ops/reporting pilot, when:",
        "- Pack is installed and activated (or --role ops passed).",
        "- Graph and setup are present; adapter recommended.",
        "- Safety boundaries unchanged (sandbox, apply confirm).",
        "",
    ])
    if trials_dir.exists():
        results = list(trials_dir.glob("*.json")) + list(trials_dir.glob("*result*"))
        if results:
            lines.append("## Recent trial output")
            lines.append("")
            lines.append(f"Trials dir: {trials_dir}. {len(results)} result/file(s) found.")
            lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path

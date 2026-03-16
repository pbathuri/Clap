"""
Persist quality_report.md for a training run (and optionally comparison outcomes).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


QUALITY_REPORT_FILENAME = "quality_report.md"


def write_quality_report(
    run_dir: Path,
    *,
    run_summary: dict[str, Any] | None = None,
    train_val_test: dict[str, int] | None = None,
    comparison_slice: dict[str, Any] | None = None,
    retrieval_impact: str | None = None,
    strengths: list[str] | None = None,
    weaknesses: list[str] | None = None,
    recommendation: str = "iterate",
) -> Path:
    """
    Write quality_report.md into run_dir.
    Loads run_summary.json from run_dir if run_summary not provided.
    """
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    if run_summary is None:
        path = run_dir / "run_summary.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                run_summary = json.load(f)
        else:
            run_summary = {}
    lines = [
        "# Quality report",
        "",
        f"- **Base model**: {run_summary.get('base_model', 'n/a')}",
        f"- **Run type**: {run_summary.get('run_type', 'full')}",
        f"- **Backend**: {run_summary.get('backend', 'n/a')}",
        f"- **Config**: {run_summary.get('llm_config_path', 'n/a')}",
        f"- **Adapter**: {run_summary.get('adapter_path', 'n/a')}",
        f"- **Success**: {run_summary.get('success', False)}",
        "",
    ]
    if train_val_test:
        lines.append("## Data")
        lines.append("")
        for k, v in train_val_test.items():
            lines.append(f"- {k}: {v}")
        lines.append("")
    if comparison_slice:
        lines.append("## Eval (this run)")
        lines.append("")
        lines.append(f"- Prediction mode: {comparison_slice.get('prediction_mode', 'n/a')}")
        lines.append(f"- Retrieval used: {comparison_slice.get('retrieval_used', False)}")
        lines.append(f"- Examples: {comparison_slice.get('num_examples', 0)}")
        for k, v in (comparison_slice.get("metrics") or {}).items():
            if isinstance(v, (int, float)):
                lines.append(f"- **{k}**: {v:.4f}" if isinstance(v, float) else f"- **{k}**: {v}")
        lines.append("")
    if retrieval_impact:
        lines.append("## Retrieval impact")
        lines.append("")
        lines.append(retrieval_impact)
        lines.append("")
    if strengths:
        lines.append("## Notable strengths")
        lines.append("")
        for s in strengths:
            lines.append(f"- {s}")
        lines.append("")
    if weaknesses:
        lines.append("## Notable weaknesses")
        lines.append("")
        for w in weaknesses:
            lines.append(f"- {w}")
        lines.append("")
    lines.append("## Recommendation")
    lines.append("")
    lines.append(recommendation)
    lines.append("")
    out = run_dir / QUALITY_REPORT_FILENAME
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return out

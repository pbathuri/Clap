"""
M17: Aggregate trial results and write readable workflow-trial report.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.trials.trial_models import WorkflowTrialResult


def load_trial_results(output_dir: Path | str) -> list[WorkflowTrialResult]:
    """Load all result JSON files from output_dir."""
    output_dir = Path(output_dir)
    if not output_dir.exists():
        return []
    results: list[WorkflowTrialResult] = []
    for path in output_dir.glob("res_*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            results.append(WorkflowTrialResult.model_validate(data))
        except Exception:
            continue
    return results


def write_trial_report(
    results: list[WorkflowTrialResult],
    output_path: Path | str,
    *,
    title: str = "Workflow trial report",
) -> Path:
    """
    Write a readable markdown report summarizing which workflows worked, where retrieval/adapter helped,
    and adoption readiness. Product-decision useful.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    by_trial: dict[str, list[WorkflowTrialResult]] = {}
    for r in results:
        by_trial.setdefault(r.trial_id, []).append(r)

    lines = [
        f"# {title}",
        "",
        f"Total results: {len(results)}",
        f"Trials: {len(by_trial)}",
        "",
        "## By trial and mode",
        "",
    ]

    for trial_id in sorted(by_trial.keys()):
        modes = by_trial[trial_id]
        lines.append(f"### {trial_id}")
        lines.append("")
        for m in sorted(modes, key=lambda x: x.model_mode):
            lines.append(f"- **{m.model_mode}** (retrieval={m.retrieval_used}, adapter={m.adapter_used})")
            lines.append(f"  - completion: {m.completion_status}")
            lines.append(f"  - task_completion: {m.task_completion_score:.2f}")
            lines.append(f"  - style_match: {m.style_match_score:.2f}")
            lines.append(f"  - retrieval_grounding: {m.retrieval_grounding_score:.2f}")
            lines.append(f"  - bundle_usefulness: {m.bundle_usefulness_score:.2f}")
            lines.append(f"  - safety: {m.safety_score:.2f}")
            if m.notes:
                lines.append(f"  - notes: {m.notes[:200]}")
            lines.append("")
        lines.append("")

    # Where retrieval helped
    lines.append("## Retrieval impact (heuristic)")
    lines.append("")
    retrieval_better: list[str] = []
    retrieval_worse: list[str] = []
    for trial_id, modes in by_trial.items():
        adapter_only = next((m for m in modes if m.model_mode == "adapter" and not m.retrieval_used), None)
        adapter_ret = next((m for m in modes if m.model_mode == "adapter_retrieval"), None)
        if adapter_only and adapter_ret:
            if adapter_ret.task_completion_score > adapter_only.task_completion_score:
                retrieval_better.append(trial_id)
            elif adapter_ret.task_completion_score < adapter_only.task_completion_score:
                retrieval_worse.append(trial_id)
    if retrieval_better:
        lines.append("- Retrieval improved task_completion: " + ", ".join(retrieval_better[:10]))
    if retrieval_worse:
        lines.append("- Retrieval lowered task_completion: " + ", ".join(retrieval_worse[:10]))
    if not retrieval_better and not retrieval_worse:
        lines.append("- No adapter vs adapter_retrieval pairs to compare.")
    lines.append("")

    # Best / worst workflows
    lines.append("## Summary")
    lines.append("")
    avg_by_trial: dict[str, float] = {}
    for trial_id, modes in by_trial.items():
        if modes:
            avg_by_trial[trial_id] = sum(m.task_completion_score for m in modes) / len(modes)
    best = sorted(avg_by_trial.items(), key=lambda x: -x[1])[:5]
    worst = sorted(avg_by_trial.items(), key=lambda x: x[1])[:5]
    lines.append("- **Strongest trials (avg task_completion):** " + ", ".join(f"{t}({v:.2f})" for t, v in best))
    lines.append("- **Weakest trials:** " + ", ".join(f"{t}({v:.2f})" for t, v in worst))
    adoption_ready = [r for r in results if r.adoption_ready]
    lines.append(f"- **Adoption-ready results:** {len(adoption_ready)}")
    lines.append("")
    lines.append("## Product decision (fill from evidence)")
    lines.append("")
    lines.append("1. **First narrow release focus:** _Run trials and set strongest domain._")
    lines.append("2. **Strongest workflow category:** _Best avg task_completion / style_match._")
    lines.append("3. **Defer:** _Weakest or retrieval-hurt categories._")
    lines.append("4. **First-draft internal pilot:** _Yes if adoption_ready > 0 and strongest category clear._")
    lines.append("5. **Next milestone after M17:** _Tune retrieval, add SFT for deferred categories, or pilot scope._")
    lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path

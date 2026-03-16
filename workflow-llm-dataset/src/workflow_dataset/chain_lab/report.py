"""
M23A: Chain run reports — per-step report, final summary, artifact tree, failure section (F2).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.chain_lab.manifest import load_run_manifest, get_run_dir, get_latest_run_id


def resolve_run_id(run_id: str, repo_root: Path | str | None = None) -> str | None:
    """Resolve run_id; if run_id is 'latest', return get_latest_run_id. Otherwise return run_id only if manifest exists."""
    if (run_id or "").strip().lower() == "latest":
        return get_latest_run_id(repo_root)
    if run_id and load_run_manifest(run_id, repo_root):
        return run_id
    return None


def failure_report_section(
    manifest: dict[str, Any],
    chain_definition: dict[str, Any] | None = None,
) -> list[str]:
    """
    Build failure report section: failing step, artifacts already produced, whether resume is possible.
    Returns list of lines (no trailing newline per line).
    """
    lines: list[str] = []
    status = manifest.get("status", "")
    if status != "failed":
        return lines
    step_results = manifest.get("step_results") or []
    failing_index: int | None = None
    for i, s in enumerate(step_results):
        if s.get("status") == "failed":
            failing_index = i
            break
    if failing_index is None:
        return lines
    steps_def = (chain_definition or {}).get("steps") or []
    step_def = steps_def[failing_index] if failing_index < len(steps_def) else {}
    step_id = (step_results[failing_index].get("step_id") or step_results[failing_index].get("label") or str(failing_index))
    lines.append("## Failure report")
    lines.append("")
    lines.append(f"- **Failing step:** {failing_index} — {step_id}")
    lines.append(f"- **Why:** {manifest.get('failure_summary') or 'Unknown'}")
    lines.append("")
    # Artifacts already produced (all successful steps before this)
    produced: list[str] = []
    for j in range(failing_index):
        if j < len(step_results):
            for p in step_results[j].get("output_paths") or []:
                produced.append(p)
    if produced:
        lines.append("- **Artifacts already produced:**")
        for p in produced[:15]:
            lines.append(f"  - `{p}`")
        if len(produced) > 15:
            lines.append(f"  - ... and {len(produced) - 15} more")
        lines.append("")
    # Resume possible if next step is resumable (default True)
    resumable = step_def.get("resumable", True)
    lines.append(f"- **Resume possible:** {'Yes' if resumable else 'No (step not resumable)'}")
    lines.append("")
    return lines


def chain_run_report(
    run_id: str,
    repo_root: Path | str | None = None,
    *,
    include_failure_section: bool = True,
    include_step_contract: bool = True,
) -> str:
    """Human-readable per-step report + final run summary. run_id may be 'latest'. Returns markdown string."""
    resolved = resolve_run_id(run_id, repo_root)
    if not resolved:
        return f"# Chain run: {run_id}\n\nRun not found or invalid (use run_id or 'latest').\n"
    manifest = load_run_manifest(resolved, repo_root)
    if not manifest:
        return f"# Chain run: {resolved}\n\nRun not found or invalid manifest.\n"
    chain_id = manifest.get("chain_id", "")
    chain_definition: dict[str, Any] | None = None
    if chain_id and include_step_contract:
        try:
            from workflow_dataset.chain_lab.definition import load_chain
            chain_definition = load_chain(chain_id, repo_root)
        except Exception:
            pass
    lines = [
        "# Chain run report",
        "",
        f"- **Run ID:** {manifest.get('run_id', resolved)}",
        f"- **Chain ID:** {manifest.get('chain_id', '')}",
        f"- **Variant:** {manifest.get('variant_label', '') or '(none)'}",
        f"- **Status:** {manifest.get('status', '')}",
        f"- **Started:** {manifest.get('started_at', '')}",
        f"- **Ended:** {manifest.get('ended_at', '')}",
        "",
    ]
    if manifest.get("failure_summary"):
        lines.append(f"**Failure summary:** {manifest['failure_summary']}")
        lines.append("")
    if include_failure_section and manifest.get("status") == "failed":
        lines.extend(failure_report_section(manifest, chain_definition))
    steps = manifest.get("step_results") or []
    steps_def = (chain_definition or {}).get("steps") or []
    lines.append("## Steps")
    lines.append("")
    for s in steps:
        idx = s.get("step_index", 0)
        step_id = s.get("step_id", "")
        label = s.get("label", "")
        status = s.get("status", "")
        err = s.get("error", "")
        step_def = steps_def[idx] if idx < len(steps_def) else {}
        lines.append(f"### Step {idx}: {step_id or label or '(unnamed)'}")
        lines.append("")
        lines.append(f"- Status: {status}")
        lines.append(f"- Started: {s.get('started_at', '')}")
        lines.append(f"- Ended: {s.get('ended_at', '')}")
        if include_step_contract and step_def:
            exp_in = step_def.get("expected_inputs") or []
            exp_out = step_def.get("expected_outputs") or []
            resumable = step_def.get("resumable", True)
            if exp_in or exp_out or "resumable" in step_def:
                lines.append(f"- Contract: inputs={exp_in!r}, outputs={exp_out!r}, resumable={resumable}")
        if err:
            lines.append(f"- Error: {err}")
        out_paths = s.get("output_paths") or []
        if out_paths:
            lines.append("- Outputs:")
            for p in out_paths[:10]:
                lines.append(f"  - `{p}`")
            if len(out_paths) > 10:
                lines.append(f"  - ... and {len(out_paths) - 10} more")
        lines.append("")
    lines.append("---")
    lines.append(f"*Report for run_id={resolved}*")
    return "\n".join(lines)


def chain_artifact_tree(run_id: str, repo_root: Path | str | None = None) -> dict[str, Any]:
    """Return artifact tree for a run: run_dir, steps with paths. run_id may be 'latest'."""
    resolved = resolve_run_id(run_id, repo_root)
    if not resolved:
        return {"run_id": run_id, "error": "run not found"}
    manifest = load_run_manifest(resolved, repo_root)
    if not manifest:
        return {"run_id": resolved, "error": "run not found"}
    root = get_run_dir(resolved, repo_root, create=False)
    tree: dict[str, Any] = {
        "run_id": resolved,
        "chain_id": manifest.get("chain_id", ""),
        "status": manifest.get("status", ""),
        "run_dir": str(root),
        "steps": [],
    }
    for s in manifest.get("step_results") or []:
        tree["steps"].append({
            "step_index": s.get("step_index"),
            "step_id": s.get("step_id", ""),
            "status": s.get("status", ""),
            "output_paths": s.get("output_paths") or [],
        })
    return tree

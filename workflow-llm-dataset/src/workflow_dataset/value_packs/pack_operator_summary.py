"""
M24H.1: Pack-specific operator summary — first-value steps, demo assets, golden bundle, expected outputs, next step.
Extends generic operator summary with value-pack context.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.value_packs.registry import get_value_pack
from workflow_dataset.value_packs.golden_bundles import get_golden_bundle
from workflow_dataset.value_packs.first_run_flow import get_sample_asset_path, build_first_run_flow


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd()


def build_pack_operator_summary(
    pack_id: str,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Build pack-specific operator summary: pack meta, first-value steps, demo assets (resolved paths),
    golden bundle ref, expected outputs, trust notes, recommended next step.
    """
    root = _repo_root(repo_root)
    pack = get_value_pack(pack_id)
    if not pack:
        return {
            "pack_id": pack_id,
            "error": f"Value pack not found: {pack_id}",
            "first_value_steps": [],
            "demo_assets": [],
            "golden_bundle": None,
            "expected_outputs": [],
            "trust_notes": "",
            "next_step": "",
        }

    flow = build_first_run_flow(pack_id, root)
    steps = flow.get("steps") or []
    demo_assets: list[dict[str, Any]] = []
    for rel in pack.sample_asset_paths or []:
        path = get_sample_asset_path(rel, root)
        demo_assets.append({"relative": rel, "resolved": str(path) if path else None, "exists": path is not None and path.exists()})

    golden = get_golden_bundle(pack_id)
    golden_ref = None
    if golden:
        golden_ref = {
            "bundle_id": golden.bundle_id,
            "display_name": golden.display_name,
            "example_job_id": golden.example_job_id,
            "example_routine_id": golden.example_routine_id,
            "example_macro_id": golden.example_macro_id,
            "first_simulate_command": golden.first_simulate_command,
            "first_real_command": golden.first_real_command,
            "sample_input_refs": golden.sample_input_refs,
        }

    next_step = ""
    if steps:
        for s in steps:
            if s.get("title") == "First simulate run":
                next_step = s.get("command", "")
                break
    if not next_step and golden:
        next_step = golden.first_simulate_command

    return {
        "pack_id": pack_id,
        "pack_name": pack.name,
        "pack_description": pack.description or "",
        "error": "",
        "first_value_steps": steps,
        "demo_assets": demo_assets,
        "golden_bundle": golden_ref,
        "expected_outputs": list(pack.expected_outputs or []),
        "trust_notes": pack.benchmark_trust_notes or "",
        "simulate_only_summary": pack.simulate_only_summary or "",
        "approvals_likely_needed": list(pack.approvals_likely_needed or []),
        "next_step": next_step,
    }


def format_pack_operator_summary(summary: dict[str, Any]) -> str:
    """Format pack operator summary for CLI or docs."""
    if summary.get("error"):
        return f"Error: {summary['error']}"
    lines = [
        f"=== Pack operator summary: {summary.get('pack_id', '')} ===",
        "",
        f"Pack: {summary.get('pack_name', '')}",
        f"Description: {summary.get('pack_description', '')}",
        "",
        "[First-value steps]",
    ]
    for s in summary.get("first_value_steps") or []:
        lines.append(f"  {s.get('step')}. {s.get('title')}: {s.get('command', '')}")
    lines.append("")
    lines.append("[Demo assets]")
    for a in summary.get("demo_assets") or []:
        status = "ok" if a.get("exists") else "missing"
        lines.append(f"  {a.get('relative', '')}  ({status})")
    lines.append("")
    if summary.get("golden_bundle"):
        g = summary["golden_bundle"]
        lines.append("[Golden bundle]")
        lines.append(f"  {g.get('display_name', '')}  bundle_id={g.get('bundle_id', '')}")
        lines.append(f"  example_job={g.get('example_job_id', '')}  example_routine={g.get('example_routine_id', '')}  example_macro={g.get('example_macro_id', '')}")
        lines.append(f"  first_simulate: {g.get('first_simulate_command', '')}")
        lines.append("")
    lines.append("[Expected outputs]")
    for o in summary.get("expected_outputs") or []:
        lines.append(f"  - {o}")
    lines.append("")
    if summary.get("trust_notes"):
        lines.append(f"[Trust] {summary['trust_notes']}")
    if summary.get("approvals_likely_needed"):
        lines.append(f"[Approvals] {', '.join(summary['approvals_likely_needed'])}")
    lines.append("")
    lines.append(f"Recommended next step: {summary.get('next_step', '')}")
    return "\n".join(lines)

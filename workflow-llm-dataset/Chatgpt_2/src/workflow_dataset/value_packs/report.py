"""
M24B: Format value pack show, recommend, first-run flow, and compare.
"""

from __future__ import annotations

from typing import Any

from workflow_dataset.value_packs.models import ValuePack


def format_pack_show(pack: ValuePack | None, pack_id: str = "") -> str:
    if not pack:
        return f"Value pack not found: {pack_id or '(no id)'}."
    lines = [
        f"=== Value pack: {pack.pack_id} ===",
        "",
        f"Name: {pack.name}",
        f"Description: {pack.description}",
        "",
        "[Target]",
        f"  field: {pack.target_field}  job_family: {pack.target_job_family}",
        "",
        "[Recommendations]",
        f"  starter_kit: {pack.starter_kit_id}  domain_pack: {pack.domain_pack_id}",
        f"  runtime_task_class: {pack.recommended_runtime_task_class}  model_class: {pack.recommended_model_class}",
        f"  jobs: {', '.join(pack.recommended_job_ids) or '—'}",
        f"  routines: {', '.join(pack.recommended_routine_ids) or '—'}",
        f"  macros: {', '.join(pack.recommended_macro_ids) or '—'}",
        "",
        "[Trust / benchmark]",
        f"  {pack.benchmark_trust_notes or '—'}",
        f"  approvals_likely_needed: {', '.join(pack.approvals_likely_needed) or '—'}",
        "",
        "[Simulate-only]",
        f"  {pack.simulate_only_summary or '—'}",
        "",
        "Expected outputs: " + "; ".join(pack.expected_outputs) if pack.expected_outputs else "",
        "",
    ]
    if pack.sample_asset_paths:
        lines.append("Sample assets: " + ", ".join(pack.sample_asset_paths))
        lines.append("")
    if pack.first_value_sequence:
        lines.append("[First-value sequence]")
        for s in pack.first_value_sequence:
            lines.append(f"  {s.step_number}. {s.title}: {s.command}")
            if s.what_user_sees:
                lines.append(f"      → {s.what_user_sees}")
            if s.what_to_do_next:
                lines.append(f"      Next: {s.what_to_do_next}")
        lines.append("")
    return "\n".join(lines).strip()


def format_recommendation(result: dict[str, Any]) -> str:
    pack = result.get("pack")
    score = result.get("score", 0)
    reason = result.get("reason", "")
    alternatives = result.get("alternatives", [])
    missing = result.get("missing_prerequisites", [])
    sim = result.get("simulate_only_summary", "")
    lines = [
        "=== Value pack recommendation ===",
        "",
        f"Recommended: {pack.name if pack else '—'} ({pack.pack_id if pack else ''})",
        f"Score: {score}",
        f"Reason: {reason}",
        "",
    ]
    if sim:
        lines.append(f"[Simulate-only] {sim}")
        lines.append("")
    if missing:
        lines.append("[Missing prerequisites]")
        for m in missing:
            lines.append(f"  - {m}")
        lines.append("")
    if alternatives:
        lines.append("[Alternatives]")
        for p, s in alternatives[:5]:
            lines.append(f"  {p.pack_id}  (score={s})  {p.name}")
        lines.append("")
    if pack:
        lines.append("Show: workflow-dataset value-packs show --id " + pack.pack_id)
        lines.append("First run: workflow-dataset value-packs first-run --id " + pack.pack_id)
        lines.append("External capabilities (for this machine/domain): workflow-dataset capabilities external recommend")
    return "\n".join(lines)


def format_first_run_flow(result: dict[str, Any]) -> str:
    pack_id = result.get("pack_id", "")
    pack = result.get("pack")
    steps = result.get("steps", [])
    if result.get("error"):
        return f"Error: {result['error']}"
    if not pack:
        return f"Pack not found: {pack_id}."
    lines = [
        f"=== First-value flow: {pack_id} ===",
        "",
    ]
    for st in steps:
        lines.append(f"{st['step']}. {st['title']}")
        lines.append(f"   Command: {st['command']}")
        if st.get("what_user_sees"):
            lines.append(f"   What you see: {st['what_user_sees']}")
        if st.get("what_to_do_next"):
            lines.append(f"   Next: {st['what_to_do_next']}")
        lines.append("")
    return "\n".join(lines).strip()


def format_compare(result: dict[str, Any]) -> str:
    if result.get("error"):
        return f"Error: {result['error']}"
    a = result.get("pack_a")
    b = result.get("pack_b")
    if not a or not b:
        return "Missing pack."
    lines = [
        "=== Value pack comparison ===",
        "",
        f"Pack A: {a.pack_id}  ({a.name})",
        f"Pack B: {b.pack_id}  ({b.name})",
        "",
        f"Score A: {result.get('score_a', 0)}  Score B: {result.get('score_b', 0)}",
        f"Fits profile better: {result.get('which_fits_better', '—')}",
        "",
        "[Missing prerequisites]",
        f"  A: {result.get('missing_prerequisites_a', [])}",
        f"  B: {result.get('missing_prerequisites_b', [])}",
        "",
        "[Overlap]",
        f"  jobs: {result.get('overlap_jobs', [])}",
        f"  routines: {result.get('overlap_routines', [])}",
        "",
        "[Simulate-only]",
        f"  A: {(result.get('simulate_only_summary_a') or '')[:80]}...",
        f"  B: {(result.get('simulate_only_summary_b') or '')[:80]}...",
    ]
    return "\n".join(lines)

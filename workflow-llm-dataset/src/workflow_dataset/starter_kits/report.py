"""
M23Y: Format starter kit show, recommendation, and first-value flow.
"""

from __future__ import annotations

from typing import Any

from workflow_dataset.starter_kits.models import StarterKit, FirstValueFlow
from workflow_dataset.starter_kits.registry import get_kit
from workflow_dataset.starter_kits.recommend import recommend_kit_from_profile


def format_kit_show(kit: StarterKit | None, kit_id: str = "") -> str:
    """Format single kit for display."""
    if not kit:
        return f"Starter kit not found: {kit_id or '(no id)'}."
    lines = [
        f"=== Starter kit: {kit.kit_id} ===",
        "",
        f"Name: {kit.name}",
        f"Description: {kit.description}",
        "",
        "[Target]",
        f"  field: {kit.target_field}  job_family: {kit.target_job_family}",
        "",
        "[Recommendations]",
        f"  domain_pack: {kit.domain_pack_id}",
        f"  runtime_task_class: {kit.recommended_runtime_task_class}  model_class: {kit.recommended_model_class}",
        f"  jobs: {', '.join(kit.recommended_job_ids) or '—'}",
        f"  routines: {', '.join(kit.recommended_routine_ids) or '—'}",
        "",
        "[First-value workflow]",
        f"  first_simulate_only: {kit.first_simulate_only_workflow or '—'}",
        "",
        "[Trust / approvals]",
        f"  {kit.trusted_real_eligibility_notes or '—'}",
        f"  approvals_likely_needed: {', '.join(kit.approvals_likely_needed) or '—'}",
        "",
        "Expected outputs: " + "; ".join(kit.expected_outputs) if kit.expected_outputs else "",
        "",
    ]
    if kit.first_value_flow:
        fvf = kit.first_value_flow
        lines.append("[First-value flow]")
        lines.append(f"  Run: {fvf.first_run_command}")
        lines.append(f"  Get back: {fvf.what_user_gets_back}")
        lines.append(f"  Why useful: {fvf.why_useful}")
        lines.append(f"  Next: {fvf.what_to_do_next}")
        lines.append("")
    return "\n".join(lines).strip()


def format_recommendation(result: dict[str, Any]) -> str:
    """Format recommend_kit_from_profile result."""
    kit = result.get("kit")
    score = result.get("score", 0)
    reason = result.get("reason", "")
    alternatives = result.get("alternatives", [])
    missing = result.get("missing_prerequisites", [])
    lines = [
        "=== Starter kit recommendation ===",
        "",
        f"Recommended: {kit.name if kit else '—'} ({kit.kit_id if kit else ''})",
        f"Score: {score}",
        f"Reason: {reason}",
        "",
    ]
    if missing:
        lines.append("[Missing prerequisites]")
        for m in missing:
            lines.append(f"  - {m}")
        lines.append("")
    if alternatives:
        lines.append("[Alternatives]")
        for k, s in alternatives[:5]:
            lines.append(f"  {k.kit_id}  (score={s})  {k.name}")
        lines.append("")
    lines.append("Show details: workflow-dataset kits show --id " + (kit.kit_id if kit else "KIT_ID"))
    lines.append("First run: workflow-dataset kits first-run --id " + (kit.kit_id if kit else "KIT_ID"))
    return "\n".join(lines)


def format_first_run_flow(kit: StarterKit | None, kit_id: str = "") -> str:
    """Format first-value flow only (what to run first, get back, next)."""
    if not kit:
        return f"Kit not found: {kit_id or '(no id)'}."
    fvf = kit.first_value_flow
    if not fvf:
        return f"Kit {kit.kit_id} has no first-value flow defined."
    lines = [
        f"=== First-value flow: {kit.kit_id} ===",
        "",
        "1. Run (simulate-first):",
        f"   {fvf.first_run_command}",
        "",
        "2. What you get back:",
        f"   {fvf.what_user_gets_back}",
        "",
        "3. Why useful:",
        f"   {fvf.why_useful}",
        "",
        "4. What to do next:",
        f"   {fvf.what_to_do_next}",
        "",
    ]
    return "\n".join(lines)

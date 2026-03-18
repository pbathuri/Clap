"""
M24A: Report formatting for list, recommend, blocked, plan, explain.
"""

from __future__ import annotations

from typing import Any

from workflow_dataset.external_capability.schema import ExternalCapabilitySource
from workflow_dataset.external_capability.planner import (
    PlannerResult,
    ActivationRecommendation,
    BlockedEntry,
)


def format_external_list(sources: list[ExternalCapabilitySource]) -> str:
    """Format external capability list for CLI."""
    lines = ["External capability sources", "---"]
    for s in sources:
        status = s.activation_status or "unknown"
        en = "enabled" if s.enabled else "disabled"
        lines.append(f"  {s.source_id}  category={s.category}  status={status}  {en}")
    return "\n".join(lines)


def format_recommend(result: PlannerResult) -> str:
    """Format recommendation output."""
    lines = ["Recommended external capabilities", "---"]
    for r in result.recommended:
        lines.append(f"  {r.source_id}  reason={r.reason}  resource={r.estimated_resource or 'medium'}")
    if not result.recommended:
        lines.append("  (none)")
    lines.append("")
    lines.append("Prerequisite steps:")
    for p in result.prerequisite_steps:
        lines.append(f"  - {p}")
    if not result.prerequisite_steps:
        lines.append("  (none)")
    lines.append("")
    lines.append(f"Resource estimate: {result.resource_estimate}")
    return "\n".join(lines)


def format_blocked(result: PlannerResult) -> str:
    """Format blocked and rejected output."""
    lines = ["Blocked / rejected external capabilities", "---"]
    lines.append("Rejected by policy:")
    for b in result.rejected_by_policy:
        lines.append(f"  {b.source_id}  reason={b.reason}  code={b.code or b.reason}")
    lines.append("Not worth it on this profile:")
    for b in result.not_worth_it:
        lines.append(f"  {b.source_id}  reason={b.reason}")
    if not result.rejected_by_policy and not result.not_worth_it:
        lines.append("  (none)")
    return "\n".join(lines)


def format_plan(steps: list[dict[str, Any]], source_id: str) -> str:
    """Format activation plan steps."""
    lines = [f"Activation plan for source: {source_id}", "---"]
    for i, s in enumerate(steps, 1):
        action = s.get("action", "step")
        detail = s.get("detail", "")
        safe = " (safe local)" if s.get("safe_local") else ""
        lines.append(f"  {i}. [{action}]{safe} {detail}")
    return "\n".join(lines)


def format_explain(source: ExternalCapabilitySource | None, source_id: str) -> str:
    """Format explain output for a single source."""
    if not source:
        return f"Source '{source_id}' not found in external capability registry."
    lines = [
        f"Explain: {source_id}",
        "---",
        f"  category: {source.category}",
        f"  display_name: {source.display_name or source_id}",
        f"  local: {source.local}  optional_remote: {source.optional_remote}",
        f"  activation_status: {source.activation_status}  enabled: {source.enabled}",
        f"  estimated_resource: {source.estimated_resource or 'medium'}",
        f"  supported_task_classes: {source.supported_task_classes}",
        f"  supported_tiers: {source.supported_tiers}",
        f"  license_policy: {source.license_policy}  usage_policy: {source.usage_policy}",
        f"  security_notes: {source.security_notes}",
        f"  approval_notes: {source.approval_notes}",
        f"  trust_notes: {source.trust_notes}",
        "  install_prerequisites:",
    ]
    for p in (source.install_prerequisites or []):
        lines.append(f"    - {p}")
    if source.notes:
        lines.append(f"  notes: {source.notes}")
    return "\n".join(lines)


def format_preview(preview: Any) -> str:
    """Format activation preview for CLI (M24D)."""
    lines = [
        f"Activation preview: {preview.activation_id}",
        "---",
        f"  source_id: {preview.source_id}  action: {preview.requested_action}",
        f"  approval_required: {preview.approval_required}  blocked: {preview.blocked}  safe_to_proceed: {preview.safe_to_proceed}",
        "",
        "What would change:",
    ]
    for w in (preview.what_would_change or []):
        lines.append(f"  - {w}")
    if preview.files_or_configs_affected:
        lines.append("Files/configs affected:")
        for f in preview.files_or_configs_affected:
            lines.append(f"  - {f}")
    if preview.block_reason:
        lines.append(f"Block reason: {preview.block_reason}")
    if preview.steps_summary:
        lines.append("Steps summary:")
        for s in preview.steps_summary[:10]:
            lines.append(f"  - {s[:80]}{'...' if len(s) > 80 else ''}")
    return "\n".join(lines)


def format_activation_request(request: Any) -> str:
    """Format activation request for CLI (M24D)."""
    lines = [
        f"Activation request: {request.activation_id}",
        "---",
        f"  source_id: {request.source_id}  category: {request.source_category}  action: {request.requested_action}",
        f"  status: {request.status}  reversible: {request.reversible}",
        f"  created_at: {request.created_at}",
    ]
    return "\n".join(lines)


def format_history(entries: list[dict[str, Any]]) -> str:
    """Format activation history for CLI (M24D)."""
    lines = ["Activation history (recent)", "---"]
    for e in entries:
        act_id = e.get("activation_id", "")
        outcome = e.get("outcome", "")
        rec = e.get("recorded_at", "")
        lines.append(f"  {act_id}  outcome={outcome}  recorded={rec}")
    if not entries:
        lines.append("  (none)")
    return "\n".join(lines)


# ----- M24G.1 Compatibility and capability recommendation -----


def format_compatibility_report(matrix: list[Any]) -> str:
    """Format compatibility matrix for CLI: source -> domains, value packs, kits, tiers."""
    from workflow_dataset.external_capability.compatibility import CompatibilityRow
    lines = ["=== Capability compatibility matrix ===", ""]
    for row in matrix:
        lines.append(f"  {row.source_id}  category={row.category}  status={row.activation_status}  enabled={row.enabled}")
        lines.append(f"    domains: {', '.join(row.compatible_domain_pack_ids[:8]) or '—'}")
        lines.append(f"    value_packs: {', '.join(row.compatible_value_pack_ids[:8]) or '—'}")
        lines.append(f"    starter_kits: {', '.join(row.compatible_starter_kit_ids[:5]) or '—'}")
        lines.append(f"    tiers: {', '.join(row.compatible_tiers) or '—'}")
        lines.append("")
    if not matrix:
        lines.append("  (no sources)")
    return "\n".join(lines).strip()


def format_capability_recommendation(result: Any) -> str:
    """Format CapabilityRecommendationResult: worth enabling, not worth, blocked, pack context."""
    lines = [
        "=== Capability recommendation ===",
        "",
        f"Pack context: value_pack={result.pack_context.get('value_pack_id') or '—'}  domain_pack={result.pack_context.get('domain_pack_id') or '—'}  task_class={result.pack_context.get('task_class') or '—'}  tier={result.pack_context.get('tier') or '—'}",
        "",
        "[Worth enabling]",
    ]
    for e in result.worth_enabling:
        lines.append(f"  {e.source_id}  reason={e.reason}  compatible={e.compatible_with_pack}  resource={e.estimated_resource or '—'}")
    if not result.worth_enabling:
        lines.append("  (none)")
    lines.append("")
    lines.append("[Not worth enabling for this pack]")
    for e in result.not_worth_enabling:
        lines.append(f"  {e.source_id}  reason={e.reason}  code={e.code}")
    if not result.not_worth_enabling:
        lines.append("  (none)")
    lines.append("")
    lines.append("[Blocked / rejected]")
    for e in result.blocked:
        lines.append(f"  {e.source_id}  reason={e.reason}  code={e.code}")
    if not result.blocked:
        lines.append("  (none)")
    return "\n".join(lines)

"""
M23D-F1: Capability profile report. Text summary of adapters, approved paths/apps, action scopes.
"""

from __future__ import annotations

from workflow_dataset.capability_discovery.models import CapabilityProfile


def format_profile_report(profile: CapabilityProfile) -> str:
    """Format capability profile as a text report."""
    lines: list[str] = []
    lines.append("# Capability profile")
    lines.append("")
    lines.append("## Adapters available")
    for a in profile.adapters_available:
        ex = "yes" if a.supports_real_execution else "no"
        sim = "yes" if a.supports_simulate else "no"
        lines.append(f"- **{a.adapter_id}** ({a.adapter_type})  available={a.available}  simulate={sim}  real_execution={ex}  actions={a.action_count}")
        if a.executable_action_ids:
            lines.append(f"  executable_actions: {', '.join(a.executable_action_ids)}")
    lines.append("")
    lines.append("## Approved paths")
    if profile.approved_paths:
        for p in profile.approved_paths:
            lines.append(f"- {p}")
    else:
        lines.append("- (none in registry)")
    lines.append("")
    lines.append("## Approved apps")
    for app in profile.approved_apps:
        lines.append(f"- {app}")
    lines.append("")
    lines.append("## Action scopes (simulate vs executable)")
    for s in profile.action_scopes:
        kind = "executable" if s.executable else "simulate_only"
        lines.append(f"- {s.adapter_id}.{s.action_id}  {kind}")
    return "\n".join(lines)

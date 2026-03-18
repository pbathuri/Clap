"""M51D: Text reports for demo USB flow."""

from __future__ import annotations

from workflow_dataset.demo_usb.models import BootstrapReadinessReport, DemoBootstrapRun


def format_readiness_report_text(rep: BootstrapReadinessReport) -> str:
    lines = [
        "=== USB demo readiness ===",
        f"Capability: {rep.capability_level.value.upper()}",
        f"Ready for onboarding: {rep.ready_for_onboarding}",
        "",
    ]
    if rep.capability_level.value == "blocked":
        lines.append(f"Blocked: {rep.blocked_reason.value or 'unknown'}")
        lines.append(rep.blocked_detail or "")
        lines.append("")
    if rep.degraded_mode.value != "none":
        lines.append(f"Degraded mode: {rep.degraded_mode.value}")
        lines.append(rep.degraded_explanation or "")
        lines.append("")
    if rep.host_profile:
        hp = rep.host_profile
        lines.append("Host:")
        lines.append(f"  Python {hp.python_version}  ok={hp.python_ok}")
        lines.append(f"  Platform: {hp.platform_system}")
        lines.append(f"  Disk free (host area): ~{hp.disk_free_mb} MB")
        if hp.ram_total_mb:
            lines.append(f"  RAM: ~{hp.ram_total_mb} MB")
        lines.append(f"  Bundle writable: {hp.bundle_writable}")
        lines.append(f"  Host workspace: {hp.host_workspace_path}")
        lines.append("")
    if rep.onboarding_next_steps:
        lines.append("Next steps:")
        for s in rep.onboarding_next_steps:
            lines.append(f"  • {s}")
    return "\n".join(lines)


def format_degraded_report_text(rep: BootstrapReadinessReport) -> str:
    if rep.capability_level.value != "degraded":
        return f"Not in degraded mode (current: {rep.capability_level.value}).\n" + format_readiness_report_text(
            rep
        )
    lines = [
        "=== Degraded demo mode ===",
        rep.degraded_explanation or "(no detail)",
        "",
        "Operational notes:",
        "  • Prefer: package install-check, edge readiness, operator quickstart.",
        "  • Avoid: large model loads or long-running training on this host.",
        "",
    ]
    return "\n".join(lines)


def format_bootstrap_flow_text(run: DemoBootstrapRun) -> str:
    lines = [
        "=== Demo bootstrap run ===",
        f"run_id: {run.run_id}",
        f"started: {run.started_at_utc}",
        f"finished: {run.finished_at_utc}",
        f"host_workspace: {run.host_workspace_path}",
        f"host_workspace_state: {run.host_workspace_state.value}",
        f"first_run_invoked: {run.first_run_invoked}",
        "",
    ]
    for log in run.log_lines:
        lines.append(f"  log: {log}")
    if run.created_paths:
        lines.append("Created / updated:")
        for p in run.created_paths[:20]:
            lines.append(f"  {p}")
        if len(run.created_paths) > 20:
            lines.append(f"  ... +{len(run.created_paths) - 20} more")
    if run.errors:
        lines.append("Errors:")
        for e in run.errors:
            lines.append(f"  ! {e}")
    if run.readiness:
        lines.append("")
        lines.append(format_readiness_report_text(run.readiness))
    return "\n".join(lines)


def format_env_report_text(d: dict) -> str:
    lines = ["=== Demo environment (host + bundle) ===", ""]
    lines.append(f"bundle_root: {d.get('bundle_root', '')}")
    b = d.get("bundle") or {}
    lines.append(
        f"bundle_writable={b.get('bundle_writable')}  "
        f"settings={b.get('has_settings_yaml')}  via={b.get('resolved_via')}"
    )
    h = d.get("host") or {}
    lines.append("")
    lines.append("Host profile:")
    for k, v in sorted(h.items()):
        if k == "check_messages" and isinstance(v, list):
            lines.append(f"  {k}:")
            for m in v[:12]:
                lines.append(f"    - {m}")
        elif isinstance(v, dict):
            lines.append(f"  {k}: {v}")
        else:
            lines.append(f"  {k}: {v}")
    return "\n".join(lines)

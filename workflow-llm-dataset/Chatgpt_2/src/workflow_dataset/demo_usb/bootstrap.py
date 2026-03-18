"""
M51C: USB demo bootstrap flow + readiness classification.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone

    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

from workflow_dataset.demo_usb.bundle_root import bundle_resolution_source
from workflow_dataset.demo_usb.config_load import load_demo_usb_config
from workflow_dataset.demo_usb.host_analysis import (
    analyze_host_environment,
    default_host_workspace,
    _test_write_dir,
)
from workflow_dataset.demo_usb.models import (
    BlockedStartupReason,
    BootstrapReadinessReport,
    DemoBootstrapRun,
    DemoCapabilityLevel,
    DegradedDemoMode,
    HostWorkspaceInitState,
    UsbDemoBundle,
)


def build_usb_demo_bundle(bundle_root: Path, resolved_via: str) -> UsbDemoBundle:
    root = bundle_root.resolve()
    bw = _test_write_dir(root / "data" / "local" / "demo_usb_probe")
    # cleanup probe dir empty parent chain optional
    try:
        probe = root / "data" / "local" / "demo_usb_probe"
        if probe.is_dir() and not any(probe.iterdir()):
            probe.rmdir()
    except OSError:
        pass
    return UsbDemoBundle(
        bundle_root=str(root),
        marker_valid=True,
        has_settings_yaml=(root / "configs" / "settings.yaml").is_file(),
        has_src_package=(root / "src" / "workflow_dataset").is_dir(),
        bundle_writable=bw,
        resolved_via=resolved_via,
    )


def build_readiness_report(
    bundle_root: Path,
    explicit_bundle: Path | str | None = None,
    host_workspace: Path | str | None = None,
) -> BootstrapReadinessReport:
    """
    Classify full / degraded / blocked without mutating bundle (except optional probe dir cleanup).
    """
    cfg = load_demo_usb_config(bundle_root)
    via = bundle_resolution_source(explicit_bundle)
    bundle = build_usb_demo_bundle(bundle_root, via)
    host_ws = Path(host_workspace).resolve() if host_workspace else default_host_workspace(bundle_root)
    profile = analyze_host_environment(bundle, bundle_root, host_workspace=host_ws)

    rep = BootstrapReadinessReport(
        capability_level=DemoCapabilityLevel.BLOCKED,
        blocked_reason=BlockedStartupReason.NONE,
        blocked_detail="",
        degraded_mode=DegradedDemoMode.NONE,
        degraded_explanation="",
        ready_for_onboarding=False,
        onboarding_next_steps=[],
        host_profile=profile,
        bundle=bundle,
    )

    if not bundle.has_settings_yaml:
        rep.blocked_reason = BlockedStartupReason.SETTINGS_MISSING
        rep.blocked_detail = "configs/settings.yaml missing from bundle."
        rep.onboarding_next_steps = ["Use a complete product copy on USB or disk."]
        return rep

    if not profile.python_ok:
        rep.blocked_reason = BlockedStartupReason.PYTHON_VERSION
        rep.blocked_detail = (
            f"Python {profile.python_version} is below minimum "
            f"{cfg['python_min_major']}.{cfg['python_min_minor']}."
        )
        rep.onboarding_next_steps = ["Install Python 3.10+ on this laptop."]
        return rep

    if not bundle.bundle_writable:
        rep.blocked_reason = BlockedStartupReason.BUNDLE_READ_ONLY_NO_FALLBACK
        rep.blocked_detail = (
            "Demo bundle is not writable (common on read-only USB mounts). "
            "Copy the product folder to the laptop disk (e.g. Desktop), then run "
            "demo bootstrap from that copy."
        )
        rep.onboarding_next_steps = [
            "Copy workflow-llm-dataset folder to a writable location.",
            f"Optional host probe dir writable: {profile.host_workspace_writable}",
        ]
        return rep

    if profile.disk_free_mb < cfg["min_disk_free_mb"]:
        rep.blocked_reason = BlockedStartupReason.INSUFFICIENT_DISK
        rep.blocked_detail = (
            f"Free disk ~{profile.disk_free_mb} MB; need at least {cfg['min_disk_free_mb']} MB."
        )
        return rep

    if not profile.host_workspace_writable:
        rep.blocked_reason = BlockedStartupReason.NO_WRITE_PATH
        rep.blocked_detail = f"Cannot write host workspace {profile.host_workspace_path}."
        return rep

    edge_ready = profile.edge_checks_summary.get("ready", False)
    failed_req = int(profile.edge_checks_summary.get("failed_required", 1))
    if not edge_ready and failed_req > 0:
        # Sandbox dirs may be missing until first_run — treat as degraded if only sandbox
        only_sandbox = all(
            "sandbox_" in m or "sandbox" in m for m in profile.check_messages
        ) or not profile.check_messages
        if only_sandbox and bundle.bundle_writable:
            rep.capability_level = DemoCapabilityLevel.DEGRADED
            rep.degraded_mode = DegradedDemoMode.MINIMAL_CLI
            rep.degraded_explanation = (
                "Some paths missing before first bootstrap; run `demo bootstrap` to create them."
            )
            rep.ready_for_onboarding = True
            rep.onboarding_next_steps = [
                "Run: workflow-dataset demo bootstrap",
                "Then: workflow-dataset package first-run --skip-onboarding (or full first-run)",
                "Then: workflow-dataset onboard bootstrap",
            ]
            return rep

    degraded_bits: list[str] = []
    rep.degraded_mode = DegradedDemoMode.NONE
    if not profile.optional_llm_config_present:
        rep.degraded_mode = DegradedDemoMode.REDUCED_MODEL_PATH
        degraded_bits.append(
            "No LLM training config — model-backed demos unavailable; CLI and local workflows OK."
        )
    if profile.ram_total_mb is not None and profile.ram_total_mb < cfg["min_ram_mb_degraded_below"]:
        if rep.degraded_mode == DegradedDemoMode.NONE:
            rep.degraded_mode = DegradedDemoMode.LOW_RESOURCES
        degraded_bits.append(
            f"RAM ~{profile.ram_total_mb} MB — use lighter demo paths; avoid large local models."
        )

    if degraded_bits:
        rep.capability_level = DemoCapabilityLevel.DEGRADED
        rep.degraded_explanation = " ".join(degraded_bits)
        rep.ready_for_onboarding = True
    else:
        rep.capability_level = DemoCapabilityLevel.FULL
        rep.ready_for_onboarding = True

    rep.onboarding_next_steps = [
        "Run: workflow-dataset demo bootstrap (if not yet)",
        "Run: workflow-dataset package first-run",
        "Run: workflow-dataset onboard bootstrap",
        "Investor path: workflow-dataset demo env-report — then operator quickstart.",
    ]
    return rep


def run_demo_bootstrap(
    bundle_root: Path | None = None,
    explicit_bundle: Path | str | None = None,
    host_workspace: Path | str | None = None,
    skip_first_run: bool = False,
) -> DemoBootstrapRun:
    from workflow_dataset.demo_usb.bundle_root import resolve_demo_bundle_root

    started = utc_now_iso()
    run_id = f"demo_usb_{started[:19].replace(':', '')}"
    run = DemoBootstrapRun(
        run_id=run_id,
        started_at_utc=started,
        finished_at_utc="",
        host_workspace_state=HostWorkspaceInitState.INITIALIZING,
        log_lines=[],
        errors=[],
    )

    try:
        root = bundle_root or resolve_demo_bundle_root(explicit_bundle)
    except ValueError as e:
        run.errors.append(str(e))
        run.host_workspace_state = HostWorkspaceInitState.FAILED
        run.readiness = BootstrapReadinessReport(
            capability_level=DemoCapabilityLevel.BLOCKED,
            blocked_reason=BlockedStartupReason.BUNDLE_NOT_FOUND,
            blocked_detail=str(e),
        )
        run.finished_at_utc = utc_now_iso()
        return run

    via = bundle_resolution_source(explicit_bundle)
    bundle = build_usb_demo_bundle(root, via)
    run.bundle = bundle
    host_ws = Path(host_workspace).resolve() if host_workspace else default_host_workspace(root)
    run.host_workspace_path = str(host_ws)

    readiness = build_readiness_report(root, explicit_bundle=explicit_bundle, host_workspace=host_ws)
    run.readiness = readiness
    run.log_lines.append(f"capability={readiness.capability_level.value}")

    # Persist host-side state (inspectable, reversible)
    try:
        state_dir = host_ws / ".workflow-demo"
        state_dir.mkdir(parents=True, exist_ok=True)
        manifest = {
            "run_id": run_id,
            "bundle_root": str(root),
            "readiness": readiness.to_dict(),
        }
        (state_dir / "last_bootstrap.json").write_text(
            json.dumps(manifest, indent=2), encoding="utf-8"
        )
        run.created_paths.append(str(state_dir / "last_bootstrap.json"))
        run.host_workspace_state = HostWorkspaceInitState.READY
    except OSError as e:
        run.errors.append(f"host_state_write: {e}")
        run.host_workspace_state = HostWorkspaceInitState.FAILED

    if readiness.capability_level == DemoCapabilityLevel.BLOCKED:
        run.finished_at_utc = utc_now_iso()
        run.log_lines.append("blocked: no bundle mutation")
        return run

    # Initialize bundle data dirs + optional first_run
    try:
        from workflow_dataset.local_deployment.first_run import run_first_run

        if not skip_first_run:
            fr = run_first_run(repo_root=root, skip_onboarding=True)
            run.first_run_invoked = True
            run.created_paths.extend(fr.get("created_dirs") or [])
            if fr.get("errors"):
                run.errors.extend(fr["errors"])
            run.log_lines.append(f"install_check_passed={fr.get('install_check_passed')}")
        else:
            from workflow_dataset.local_deployment.first_run import _ensure_local_dirs

            run.created_paths.extend(_ensure_local_dirs(root))
            run.log_lines.append("dirs_only_skip_first_run")
    except Exception as e:
        run.errors.append(f"first_run: {e}")
        run.host_workspace_state = HostWorkspaceInitState.FAILED

    # Demo-local marker under bundle
    try:
        demo_dir = root / "data" / "local" / "demo_usb"
        demo_dir.mkdir(parents=True, exist_ok=True)
        (demo_dir / "bootstrap_state.yaml").write_text(
            _yaml_safe_dump(
                {
                    "run_id": run_id,
                    "finished_at_utc": utc_now_iso(),
                    "capability": readiness.capability_level.value,
                }
            ),
            encoding="utf-8",
        )
        run.created_paths.append(str(demo_dir / "bootstrap_state.yaml"))
    except OSError:
        pass

    run.finished_at_utc = utc_now_iso()
    return run


def _yaml_safe_dump(obj: dict[str, Any]) -> str:
    try:
        import yaml
        return yaml.safe_dump(obj, default_flow_style=False, allow_unicode=True)
    except Exception:
        return json.dumps(obj, indent=2)


def build_host_env_report_dict(bundle_root: Path) -> dict[str, Any]:
    """Flat dict for demo env-report command."""
    bundle = build_usb_demo_bundle(bundle_root, "inline")
    prof = analyze_host_environment(bundle, bundle_root)
    return {
        "bundle_root": str(bundle_root.resolve()),
        "host": prof.to_dict(),
        "bundle": bundle.to_dict(),
    }

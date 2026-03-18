"""
M51B: Host environment analysis for spare-laptop investor demo.
"""

from __future__ import annotations

import os
import platform
import shutil
import sys
import uuid
from pathlib import Path
from typing import Any

from workflow_dataset.demo_usb.models import HostEnvironmentProfile, UsbDemoBundle
from workflow_dataset.demo_usb.config_load import load_demo_usb_config


def _test_write_dir(d: Path) -> bool:
    try:
        d.mkdir(parents=True, exist_ok=True)
        probe = d / f".demo_usb_probe_{uuid.uuid4().hex[:8]}"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return True
    except OSError:
        return False


def _test_bundle_writable(bundle_root: Path) -> bool:
    probe_dir = bundle_root / "data" / "local"
    return _test_write_dir(probe_dir)


def default_host_workspace(bundle_root: Path) -> Path:
    """Deterministic host path for demo state (reversible: user may delete ~/.workflow-demo-host)."""
    safe = bundle_root.name.replace(" ", "_")[:48]
    return Path.home() / ".workflow-demo-host" / safe


def analyze_host_environment(
    bundle: UsbDemoBundle,
    bundle_root: Path,
    host_workspace: Path | None = None,
) -> HostEnvironmentProfile:
    cfg = load_demo_usb_config(bundle_root)
    py_min = (cfg["python_min_major"], cfg["python_min_minor"])
    cur = (sys.version_info.major, sys.version_info.minor)
    python_ok = cur >= py_min

    host_ws = (host_workspace or default_host_workspace(bundle_root)).resolve()
    host_writable = _test_write_dir(host_ws / "probe")

    prof = HostEnvironmentProfile(
        python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        python_ok=python_ok,
        platform_system=platform.system(),
        hostname_hint=platform.node()[:64],
        bundle_writable=bundle.bundle_writable,
        host_workspace_path=str(host_ws),
        host_workspace_writable=host_writable,
        disk_free_mb=0,
        ram_total_mb=None,
        cpu_count=os.cpu_count(),
        optional_llm_config_present=(bundle_root / "configs" / "llm_training_full.yaml").is_file(),
    )

    try:
        usage = shutil.disk_usage(host_ws.parent)
        prof.disk_free_mb = int(usage.free / (1024 * 1024))
    except OSError:
        prof.disk_free_mb = 0

    try:
        import psutil  # type: ignore
        prof.ram_total_mb = int(psutil.virtual_memory().total / (1024 * 1024))
    except Exception:
        prof.ram_total_mb = None

    # Edge checks against bundle (code + config on USB/copy)
    try:
        from workflow_dataset.edge.checks import run_readiness_checks, checks_summary

        checks = run_readiness_checks(repo_root=bundle_root, config_path="configs/settings.yaml")
        prof.edge_checks_summary = checks_summary(checks)
        for c in checks:
            if not c.get("passed"):
                prof.check_messages.append(f"{c.get('check_id')}: {c.get('message')}")
    except Exception as e:
        prof.edge_checks_summary = {"ready": False, "error": str(e)}
        prof.check_messages.append(f"edge_checks_error: {e}")

    return prof

"""
M51A–M51D: USB bootstrap runtime + environment readiness for investor demo.
Local-first; bounded; no cloud.
"""

from workflow_dataset.demo_usb.models import (
    DemoCapabilityLevel,
    BlockedStartupReason,
    HostWorkspaceInitState,
    DegradedDemoMode,
    UsbDemoBundle,
    HostEnvironmentProfile,
    BootstrapReadinessReport,
    DemoBootstrapRun,
)
from workflow_dataset.demo_usb.bundle_root import resolve_demo_bundle_root
from workflow_dataset.demo_usb.bootstrap import run_demo_bootstrap, build_readiness_report
from workflow_dataset.demo_usb.profiles_playbooks import (
    load_demo_bundle_profiles,
    load_usb_playbooks,
    suggest_profile_for_readiness,
    suggest_playbook_for_readiness,
)

__all__ = [
    "DemoCapabilityLevel",
    "BlockedStartupReason",
    "HostWorkspaceInitState",
    "DegradedDemoMode",
    "UsbDemoBundle",
    "HostEnvironmentProfile",
    "BootstrapReadinessReport",
    "DemoBootstrapRun",
    "resolve_demo_bundle_root",
    "run_demo_bootstrap",
    "build_readiness_report",
    "load_demo_bundle_profiles",
    "load_usb_playbooks",
    "suggest_profile_for_readiness",
    "suggest_playbook_for_readiness",
]

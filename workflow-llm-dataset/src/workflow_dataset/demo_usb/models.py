"""
M51A: Demo bootstrap models — USB investor demo cut.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class DemoCapabilityLevel(str, Enum):
    """How much of the demo can run on this host."""

    FULL = "full"
    DEGRADED = "degraded"
    BLOCKED = "blocked"


class BlockedStartupReason(str, Enum):
    """Why startup cannot proceed."""

    NONE = ""
    PYTHON_VERSION = "python_version_below_minimum"
    BUNDLE_NOT_FOUND = "bundle_root_not_found_or_invalid"
    SETTINGS_MISSING = "configs_settings_yaml_missing"
    NO_WRITE_PATH = "no_writable_workspace_bundle_or_host"
    INSUFFICIENT_DISK = "insufficient_disk_space"
    BUNDLE_READ_ONLY_NO_FALLBACK = "bundle_read_only_copy_required"


class HostWorkspaceInitState(str, Enum):
    """Host-side working area initialization."""

    NOT_STARTED = "not_started"
    INITIALIZING = "initializing"
    READY = "ready"
    FAILED = "failed"


class DegradedDemoMode(str, Enum):
    """Honest degraded demo profile."""

    NONE = "none"
    REDUCED_MODEL_PATH = "reduced_model_path_no_llm_config"
    LOW_RESOURCES = "low_resources_reduced_profile"
    MINIMAL_CLI = "minimal_cli_readiness_only"


@dataclass
class UsbDemoBundle:
    """Resolved USB-hosted demo bundle (product root on removable media or copy)."""

    bundle_root: str = ""
    marker_valid: bool = False
    has_settings_yaml: bool = False
    has_src_package: bool = False
    bundle_writable: bool = False
    resolved_via: str = ""  # explicit | env | cwd

    def to_dict(self) -> dict[str, Any]:
        return {
            "bundle_root": self.bundle_root,
            "marker_valid": self.marker_valid,
            "has_settings_yaml": self.has_settings_yaml,
            "has_src_package": self.has_src_package,
            "bundle_writable": self.bundle_writable,
            "resolved_via": self.resolved_via,
        }


@dataclass
class HostEnvironmentProfile:
    """Target laptop snapshot for demo (practical, not exhaustive hardware inventory)."""

    python_version: str = ""
    python_ok: bool = False
    platform_system: str = ""
    hostname_hint: str = ""
    bundle_writable: bool = False
    host_workspace_path: str = ""
    host_workspace_writable: bool = False
    disk_free_mb: int = 0
    ram_total_mb: int | None = None
    cpu_count: int | None = None
    optional_llm_config_present: bool = False
    edge_checks_summary: dict[str, Any] = field(default_factory=dict)
    check_messages: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "python_version": self.python_version,
            "python_ok": self.python_ok,
            "platform_system": self.platform_system,
            "hostname_hint": self.hostname_hint,
            "bundle_writable": self.bundle_writable,
            "host_workspace_path": self.host_workspace_path,
            "host_workspace_writable": self.host_workspace_writable,
            "disk_free_mb": self.disk_free_mb,
            "ram_total_mb": self.ram_total_mb,
            "cpu_count": self.cpu_count,
            "optional_llm_config_present": self.optional_llm_config_present,
            "edge_checks_summary": dict(self.edge_checks_summary),
            "check_messages": list(self.check_messages),
        }


@dataclass
class BootstrapReadinessReport:
    """Readiness for onboarding / demo launch."""

    capability_level: DemoCapabilityLevel = DemoCapabilityLevel.BLOCKED
    blocked_reason: BlockedStartupReason = BlockedStartupReason.NONE
    blocked_detail: str = ""
    degraded_mode: DegradedDemoMode = DegradedDemoMode.NONE
    degraded_explanation: str = ""
    ready_for_onboarding: bool = False
    onboarding_next_steps: list[str] = field(default_factory=list)
    host_profile: HostEnvironmentProfile | None = None
    bundle: UsbDemoBundle | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "capability_level": self.capability_level.value,
            "blocked_reason": self.blocked_reason.value,
            "blocked_detail": self.blocked_detail,
            "degraded_mode": self.degraded_mode.value,
            "degraded_explanation": self.degraded_explanation,
            "ready_for_onboarding": self.ready_for_onboarding,
            "onboarding_next_steps": list(self.onboarding_next_steps),
            "host_profile": self.host_profile.to_dict() if self.host_profile else {},
            "bundle": self.bundle.to_dict() if self.bundle else {},
        }


@dataclass
class DemoBootstrapRun:
    """Single demo bootstrap execution record."""

    run_id: str = ""
    started_at_utc: str = ""
    finished_at_utc: str = ""
    bundle: UsbDemoBundle | None = None
    host_workspace_state: HostWorkspaceInitState = HostWorkspaceInitState.NOT_STARTED
    host_workspace_path: str = ""
    readiness: BootstrapReadinessReport | None = None
    created_paths: list[str] = field(default_factory=list)
    first_run_invoked: bool = False
    log_lines: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "started_at_utc": self.started_at_utc,
            "finished_at_utc": self.finished_at_utc,
            "bundle": self.bundle.to_dict() if self.bundle else {},
            "host_workspace_state": self.host_workspace_state.value,
            "host_workspace_path": self.host_workspace_path,
            "readiness": self.readiness.to_dict() if self.readiness else {},
            "created_paths": list(self.created_paths),
            "first_run_invoked": self.first_run_invoked,
            "log_lines": list(self.log_lines),
            "errors": list(self.errors),
        }

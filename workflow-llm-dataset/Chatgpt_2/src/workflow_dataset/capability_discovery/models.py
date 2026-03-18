"""
M23D-F1: Capability discovery model. Maps adapters, approved paths/apps, and action scopes (simulate vs executable).
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ActionScope:
    """One action's scope: adapter, action, and whether it is executable (vs simulate-only)."""
    adapter_id: str
    action_id: str
    executable: bool
    supports_simulate: bool = True


@dataclass
class AdapterCapability:
    """Summary of one adapter's availability and execution support."""
    adapter_id: str
    adapter_type: str
    available: bool
    supports_simulate: bool
    supports_real_execution: bool
    action_count: int
    executable_action_ids: list[str] = field(default_factory=list)


@dataclass
class CapabilityProfile:
    """Aggregated capability view: adapters, approved paths/apps, action scopes."""
    adapters_available: list[AdapterCapability] = field(default_factory=list)
    approved_paths: list[str] = field(default_factory=list)
    approved_apps: list[str] = field(default_factory=list)
    action_scopes: list[ActionScope] = field(default_factory=list)

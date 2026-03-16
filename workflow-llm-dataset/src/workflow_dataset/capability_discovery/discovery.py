"""
M23D-F1: Capability discovery. Lightweight scan: adapters from registry + approval registry only.
"""

from __future__ import annotations

from pathlib import Path

from workflow_dataset.desktop_adapters import list_adapters, check_availability
from workflow_dataset.desktop_adapters.app_allowlist import APPROVED_APP_NAMES

from workflow_dataset.capability_discovery.models import (
    CapabilityProfile,
    AdapterCapability,
    ActionScope,
)
from workflow_dataset.capability_discovery.approval_registry import load_approval_registry, ApprovalRegistry


def run_scan(
    repo_root: Path | str | None = None,
    config_path: str | None = None,
    approval_registry: ApprovalRegistry | None = None,
) -> CapabilityProfile:
    """
    Run capability scan. Uses adapter registry and approval registry only; no filesystem scan.
    Returns CapabilityProfile with adapters_available, approved_paths, approved_apps, action_scopes.
    """
    if approval_registry is None:
        approval_registry = load_approval_registry(repo_root)
    adapters = list_adapters()
    adapter_caps: list[AdapterCapability] = []
    action_scopes: list[ActionScope] = []
    for a in adapters:
        av = check_availability(a.adapter_id)
        executable_ids = [act.action_id for act in a.supported_actions if act.supports_real]
        adapter_caps.append(AdapterCapability(
            adapter_id=a.adapter_id,
            adapter_type=a.adapter_type,
            available=av.get("available", False),
            supports_simulate=a.supports_simulate,
            supports_real_execution=a.supports_real_execution,
            action_count=len(a.supported_actions),
            executable_action_ids=executable_ids,
        ))
        for act in a.supported_actions:
            action_scopes.append(ActionScope(
                adapter_id=a.adapter_id,
                action_id=act.action_id,
                executable=act.supports_real,
                supports_simulate=act.supports_simulate,
            ))
    approved_paths = list(approval_registry.approved_paths) if approval_registry else []
    approved_apps = list(approval_registry.approved_apps) if approval_registry else []
    if not approved_apps:
        approved_apps = list(APPROVED_APP_NAMES)
    return CapabilityProfile(
        adapters_available=adapter_caps,
        approved_paths=approved_paths,
        approved_apps=approved_apps,
        action_scopes=action_scopes,
    )

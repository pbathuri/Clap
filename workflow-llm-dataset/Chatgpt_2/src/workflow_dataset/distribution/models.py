"""
M24R–M24U: Distribution models — install bundle, field deployment profile,
pack-aware installation profile, required capabilities, approvals/setup, machine assumptions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class InstallBundle:
    """Installable local product bundle: version, contents summary, required capabilities, machine assumptions."""
    bundle_id: str
    version: str
    description: str = ""
    repo_root: str = ""
    generated_at: str = ""
    # Contents summary (from current profile)
    edge_profile_summary: dict[str, Any] = field(default_factory=dict)
    readiness_summary: dict[str, Any] = field(default_factory=dict)
    required_capabilities: list[str] = field(default_factory=list)  # e.g. config_exists, python_version
    required_approvals_setup: list[str] = field(default_factory=list)  # e.g. approval_registry_optional
    machine_assumptions: dict[str, Any] = field(default_factory=dict)  # e.g. min_python, disk, platform
    product_surfaces_summary: dict[str, Any] = field(default_factory=dict)


@dataclass
class FieldDeploymentProfile:
    """Field deployment profile: target pack, prerequisites, trust/readiness, first-value run."""
    profile_id: str
    pack_id: str
    pack_name: str = ""
    description: str = ""
    repo_root: str = ""
    generated_at: str = ""
    runtime_prerequisites: list[str] = field(default_factory=list)
    pack_provisioning_prerequisites: list[str] = field(default_factory=list)
    required_capabilities: list[str] = field(default_factory=list)
    required_approvals_setup: list[str] = field(default_factory=list)
    trust_readiness_checks: list[str] = field(default_factory=list)
    first_value_run_command: str = ""
    first_value_run_notes: str = ""
    machine_assumptions: dict[str, Any] = field(default_factory=dict)


@dataclass
class PackAwareInstallProfile:
    """Pack-aware installation profile: for a given pack_id, what install and setup is required."""
    pack_id: str
    pack_name: str = ""
    required_capabilities: list[str] = field(default_factory=list)
    required_approvals_setup: list[str] = field(default_factory=list)
    runtime_prerequisites: list[str] = field(default_factory=list)
    pack_provisioning_prerequisites: list[str] = field(default_factory=list)
    machine_assumptions: dict[str, Any] = field(default_factory=dict)
    first_value_steps: list[str] = field(default_factory=list)

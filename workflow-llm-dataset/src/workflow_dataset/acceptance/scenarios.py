"""
M24C: Acceptance scenario schema — profile, machine, approvals, starter kit, first-value steps,
expected outputs, expected blocked behaviors, trust/readiness expectations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Map scenario_id -> starter_kit_id (from starter_kits.registry)
SCENARIO_KIT_MAP = {
    "founder_first_run": "founder_ops_starter",
    "analyst_first_run": "analyst_starter",
    "developer_first_run": "developer_starter",
    "document_worker_first_run": "document_worker_starter",
}


@dataclass
class AcceptanceScenario:
    """Acceptance scenario for first real-user validation."""
    scenario_id: str
    name: str
    description: str = ""
    # Assumptions
    profile_assumptions: dict[str, Any] = field(default_factory=dict)  # field, job_family, etc.
    machine_assumptions: dict[str, Any] = field(default_factory=dict)  # config_exists, edge_ready optional
    approvals_needed: list[str] = field(default_factory=list)  # path_workspace, apply_confirm, etc.
    # Pack and flow
    starter_kit_id: str = ""
    first_value_steps: list[str] = field(default_factory=list)  # journey step ids: install_readiness, bootstrap_profile, ...
    # Expectations
    expected_outputs: list[str] = field(default_factory=list)  # e.g. "Bootstrap profile exists", "Inbox returns digest"
    expected_blocked: list[str] = field(default_factory=list)  # e.g. "Real mode blocked without approval registry"
    trust_readiness_expectations: dict[str, Any] = field(default_factory=dict)  # e.g. simulate_only_available: true


BUILTIN_SCENARIOS: list[AcceptanceScenario] = [
    AcceptanceScenario(
        scenario_id="founder_first_run",
        name="New founder/operator first run",
        description="First run for a founder/operator: install, bootstrap, onboard, select founder kit, run first simulate.",
        profile_assumptions={"field": "operations", "job_family": "founder"},
        machine_assumptions={"config_exists": True},
        approvals_needed=["path_workspace", "apply_confirm"],
        starter_kit_id="founder_ops_starter",
        first_value_steps=["install_readiness", "bootstrap_profile", "onboard_approvals", "select_pack", "run_first_simulate", "inspect_trust", "inspect_inbox"],
        expected_outputs=["Install check passes or reports missing prereqs", "Bootstrap profile created or exists", "Onboarding status available", "Starter kit founder_ops_starter recommended or selectable", "First simulate workflow (morning_ops or job) can be run or reported", "Trust cockpit returns state", "Inbox returns digest or empty state"],
        expected_blocked=["Real mode blocked without approval registry", "Macro/job real run blocked until approvals"],
        trust_readiness_expectations={"simulate_only_available": True, "trust_cockpit_available": True},
    ),
    AcceptanceScenario(
        scenario_id="analyst_first_run",
        name="Analyst first run",
        description="First run for analyst/researcher: profile, kit analyst_starter, first job weekly_status_from_notes simulate.",
        profile_assumptions={"field": "research", "job_family": "analyst"},
        machine_assumptions={"config_exists": True},
        approvals_needed=["path_workspace", "apply_confirm", "data_export"],
        starter_kit_id="analyst_starter",
        first_value_steps=["install_readiness", "bootstrap_profile", "onboard_approvals", "select_pack", "run_first_simulate", "inspect_trust", "inspect_inbox"],
        expected_outputs=["Bootstrap profile exists", "analyst_starter recommended for profile", "Job weekly_status_from_notes runnable in simulate or reported as missing", "Trust cockpit and inbox available"],
        expected_blocked=["Real mode blocked without approvals", "Data export blocked until approved"],
        trust_readiness_expectations={"simulate_only_available": True},
    ),
    AcceptanceScenario(
        scenario_id="developer_first_run",
        name="Developer first run",
        description="First run for developer: coding kit, first simulate replay_cli_demo or equivalent.",
        profile_assumptions={"field": "development", "job_family": "developer"},
        machine_assumptions={"config_exists": True},
        approvals_needed=["path_repo", "apply_confirm"],
        starter_kit_id="developer_starter",
        first_value_steps=["install_readiness", "bootstrap_profile", "onboard_approvals", "select_pack", "run_first_simulate", "inspect_trust", "inspect_inbox"],
        expected_outputs=["developer_starter selectable", "First simulate workflow (replay_cli_demo or job) reported", "Trust and inbox available"],
        expected_blocked=["Real code apply blocked without approval"],
        trust_readiness_expectations={"simulate_only_available": True},
    ),
    AcceptanceScenario(
        scenario_id="document_worker_first_run",
        name="Document-heavy user first run",
        description="First run for document-heavy knowledge worker: document_worker_starter, weekly_status_from_notes simulate.",
        profile_assumptions={"field": "document", "job_family": "writer"},
        machine_assumptions={"config_exists": True},
        approvals_needed=["path_workspace", "apply_confirm"],
        starter_kit_id="document_worker_starter",
        first_value_steps=["install_readiness", "bootstrap_profile", "onboard_approvals", "select_pack", "run_first_simulate", "inspect_trust", "inspect_inbox"],
        expected_outputs=["document_worker_starter recommended", "First simulate job reported", "Inbox and trust available"],
        expected_blocked=["Real apply blocked without approvals"],
        trust_readiness_expectations={"simulate_only_available": True},
    ),
]


def list_scenarios() -> list[str]:
    """Return list of scenario IDs."""
    return [s.scenario_id for s in BUILTIN_SCENARIOS]


def get_scenario(scenario_id: str) -> AcceptanceScenario | None:
    """Return scenario by id."""
    for s in BUILTIN_SCENARIOS:
        if s.scenario_id == scenario_id:
            return s
    return None

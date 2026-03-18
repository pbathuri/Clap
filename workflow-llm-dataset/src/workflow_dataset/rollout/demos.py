"""
M24F: Guided demo definitions — required pack, capabilities, sample assets,
expected outputs, trust notes, demo steps. Maps to acceptance scenarios / starter kits.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Demo id -> acceptance scenario_id (for launch)
DEMO_TO_SCENARIO = {
    "founder_demo": "founder_first_run",
    "analyst_demo": "analyst_first_run",
    "developer_demo": "developer_first_run",
    "document_worker_demo": "document_worker_first_run",
}


@dataclass
class GuidedDemo:
    """Guided demo for operator: pack, capabilities, steps, expected outputs, trust notes."""
    demo_id: str
    name: str
    description: str = ""
    required_pack: str = ""           # starter_kit_id
    required_capabilities: list[str] = field(default_factory=list)  # e.g. config_exists, approval_registry
    recommended_sample_assets: list[str] = field(default_factory=list)  # e.g. data/local/notes/sample.md
    expected_outputs: list[str] = field(default_factory=list)
    trust_readiness_notes: str = ""
    demo_steps: list[str] = field(default_factory=list)  # ordered step labels or commands


BUILTIN_DEMOS: list[GuidedDemo] = [
    GuidedDemo(
        demo_id="founder_demo",
        name="Founder / operator demo",
        description="Demo for founder/operator: install, bootstrap, onboard, founder kit, first simulate.",
        required_pack="founder_ops_starter",
        required_capabilities=["config_exists", "edge_checks", "approval_registry_optional"],
        recommended_sample_assets=["data/local/notes", "data/local/workspaces"],
        expected_outputs=["Install check passed", "Bootstrap profile exists", "founder_ops_starter recommended", "First simulate (morning_ops or job) runnable", "Trust cockpit and inbox return state"],
        trust_readiness_notes="Simulate-first; real mode after approval registry. Demo shows trust cockpit and inbox.",
        demo_steps=["install_readiness", "bootstrap_profile", "onboard_approvals", "select_pack", "run_first_simulate", "inspect_trust", "inspect_inbox", "next_step"],
    ),
    GuidedDemo(
        demo_id="analyst_demo",
        name="Analyst demo",
        description="Demo for analyst: profile, analyst kit, first job weekly_status_from_notes simulate.",
        required_pack="analyst_starter",
        required_capabilities=["config_exists", "edge_checks", "approval_registry_optional"],
        recommended_sample_assets=["data/local/notes", "data/local/llm/corpus"],
        expected_outputs=["analyst_starter recommended", "Job weekly_status_from_notes runnable in simulate", "Trust and inbox available"],
        trust_readiness_notes="Retrieval and local adapter preferred; real mode after approvals.",
        demo_steps=["install_readiness", "bootstrap_profile", "onboard_approvals", "select_pack", "run_first_simulate", "inspect_trust", "inspect_inbox", "next_step"],
    ),
    GuidedDemo(
        demo_id="developer_demo",
        name="Developer demo",
        description="Demo for developer: coding kit, first simulate replay_cli_demo or job.",
        required_pack="developer_starter",
        required_capabilities=["config_exists", "edge_checks", "approval_registry_optional"],
        recommended_sample_assets=["data/local/task_demonstrations", "data/local/job_packs"],
        expected_outputs=["developer_starter selectable", "First simulate workflow reported", "Trust and inbox available"],
        trust_readiness_notes="Code apply only with confirm; simulate-first for task replay.",
        demo_steps=["install_readiness", "bootstrap_profile", "onboard_approvals", "select_pack", "run_first_simulate", "inspect_trust", "inspect_inbox", "next_step"],
    ),
    GuidedDemo(
        demo_id="document_worker_demo",
        name="Document-heavy user demo",
        description="Demo for document-heavy user: document_worker_starter, weekly_status_from_notes simulate.",
        required_pack="document_worker_starter",
        required_capabilities=["config_exists", "edge_checks", "approval_registry_optional"],
        recommended_sample_assets=["data/local/notes", "data/local/llm/corpus"],
        expected_outputs=["document_worker_starter recommended", "First simulate job reported", "Inbox and trust available"],
        trust_readiness_notes="Local corpus and embeddings by default; real apply after approval.",
        demo_steps=["install_readiness", "bootstrap_profile", "onboard_approvals", "select_pack", "run_first_simulate", "inspect_trust", "inspect_inbox", "next_step"],
    ),
]


def list_demos() -> list[str]:
    """Return list of demo IDs."""
    return [d.demo_id for d in BUILTIN_DEMOS]


def get_demo(demo_id: str) -> GuidedDemo | None:
    """Return demo by id."""
    for d in BUILTIN_DEMOS:
        if d.demo_id == demo_id:
            return d
    return None

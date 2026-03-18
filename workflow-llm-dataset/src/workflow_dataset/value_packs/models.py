"""
M24B: Value pack model — vertical end-user value with concrete first-value sequence and optional sample assets.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class FirstValueStep:
    """Single step in the first-value sequence."""
    step_number: int
    title: str
    command: str
    what_user_sees: str = ""
    what_to_do_next: str = ""
    run_read_only: bool = False  # True if we can run and show output without side effects


@dataclass
class ValuePack:
    """Vertical value pack: target field, recommendations, first-value sequence, benchmark/trust, sample assets."""
    pack_id: str
    name: str
    description: str = ""
    target_field: str = ""
    target_job_family: str = ""
    # Link to existing starter kit / domain pack
    starter_kit_id: str = ""
    domain_pack_id: str = ""
    # Profile and runtime
    recommended_profile_defaults: dict[str, Any] = field(default_factory=dict)
    recommended_runtime_task_class: str = ""
    recommended_model_class: str = ""
    recommended_external_capability_classes: list[str] = field(default_factory=list)
    # Jobs, routines, macros
    recommended_job_ids: list[str] = field(default_factory=list)
    recommended_routine_ids: list[str] = field(default_factory=list)
    recommended_macro_ids: list[str] = field(default_factory=list)
    # First-value: concrete sequence (install/bootstrap → first simulate → first trusted-real candidate)
    first_value_sequence: list[FirstValueStep] = field(default_factory=list)
    first_simulate_only_workflow: str = ""  # job or routine id for step "first simulate"
    first_trusted_real_candidate: str = ""   # job or routine id suggested for first real run (after approvals)
    # Trust / benchmark
    benchmark_trust_notes: str = ""
    approvals_likely_needed: list[str] = field(default_factory=list)
    expected_outputs: list[str] = field(default_factory=list)
    simulate_only_summary: str = ""
    # Optional sample assets (paths relative to data/local/value_packs/samples/)
    sample_asset_paths: list[str] = field(default_factory=list)

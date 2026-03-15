"""
M22: MiroFish simulation/workflow-scenario reference. M21 adoption: reference_only.
Workflow and scenario patterns; no import of external MiroFish code.
"""

from __future__ import annotations

REFERENCE = {
    "source_id": "mirofish",
    "adoption": "reference_only",
    "description": "Simulation and workflow-scenario reference for trials/demos.",
    "runtime_mapping": {
        "workflow_scenarios": "Trial tasks and demo flows; we use our own trial_friendly_tasks and release flows.",
        "simulation": "Controlled scenario execution; we keep sandbox and apply gates.",
    },
    "approved_patterns": [
        "Structured workflow scenarios for evaluation and demos.",
    ],
    "rejected_or_unsafe": [
        "No import of MiroFish code without explicit optional_wrapper approval.",
        "No unconstrained simulation or network access from scenarios.",
    ],
}

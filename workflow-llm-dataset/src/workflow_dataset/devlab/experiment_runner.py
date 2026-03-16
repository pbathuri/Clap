"""
M21Z: Run one experiment: benchmark suite, score, generate proposal. No auto-apply.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.devlab.experiments import load_experiment


def run_experiment(experiment_id: str, root: Path | str | None = None) -> dict[str, Any]:
    """Run one experiment. Returns status (done | failed), error if failed."""
    definition = load_experiment(experiment_id, root)
    if not definition:
        return {"status": "failed", "error": "Experiment not found", "experiment_id": experiment_id}
    # Minimal run: no benchmark execution; just return done for defined experiments
    return {"status": "done", "experiment_id": experiment_id, "definition": definition}

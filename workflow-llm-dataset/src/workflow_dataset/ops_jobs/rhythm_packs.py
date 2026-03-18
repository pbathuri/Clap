"""
M41L.1: Production rhythm packs — named weekly/monthly maintenance packs with review checklists.
"""

from __future__ import annotations

from workflow_dataset.ops_jobs.models import ProductionRhythmPack

BUILTIN_RHYTHM_PACKS: list[ProductionRhythmPack] = [
    ProductionRhythmPack(
        pack_id="weekly_production",
        name="Weekly production rhythm",
        description="Run weekly ops jobs and review supportability, adaptation, and triage.",
        rhythm="weekly",
        job_ids=["supportability_refresh", "adaptation_audit"],
        review_checklist=[
            "Review release readiness and supportability report.",
            "Review adaptation/experiment queue and devlab status.",
            "Review triage playbook and cohort health if not done daily.",
        ],
    ),
    ProductionRhythmPack(
        pack_id="monthly_production",
        name="Monthly production rhythm",
        description="Broader review for sustained deployment: deploy bundle, handoff, vertical value.",
        rhythm="monthly",
        job_ids=["supportability_refresh", "adaptation_audit", "issue_cluster_review", "production_cut_regression"],
        review_checklist=[
            "Review release handoff pack and supportability scope.",
            "Review deploy bundle health and maintenance mode report.",
            "Review vertical pack progress and first-value path.",
            "Review triage clusters and operator do-now recommendations.",
        ],
    ),
]


def get_rhythm_pack(pack_id: str) -> ProductionRhythmPack | None:
    for p in BUILTIN_RHYTHM_PACKS:
        if p.pack_id == pack_id:
            return p
    return None


def list_rhythm_pack_ids() -> list[str]:
    return [p.pack_id for p in BUILTIN_RHYTHM_PACKS]

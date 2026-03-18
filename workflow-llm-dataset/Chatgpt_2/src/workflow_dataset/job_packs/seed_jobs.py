"""
M23J: Seed example job pack. Optional.
"""

from __future__ import annotations

from pathlib import Path

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

from workflow_dataset.job_packs.schema import JobPack, JobPackSource
from workflow_dataset.job_packs.store import save_job_pack


def seed_example_job_pack(repo_root: Path | str | None = None) -> Path:
    """Create one example job pack: weekly_status_from_notes (benchmark_case -> inspect_folder_basic)."""
    now = utc_now_iso()
    job = JobPack(
        job_pack_id="weekly_status_from_notes",
        title="Weekly status from notes",
        description="Inspect local folder and list contents; can be backed by benchmark inspect_folder_basic.",
        category="reporting",
        source=JobPackSource(kind="benchmark_case", ref="inspect_folder_basic"),
        required_adapters=["file_ops"],
        required_approvals=[],
        simulate_support=True,
        real_mode_eligibility=True,
        parameter_schema={
            "path": {"type": "string", "default": "data/local", "required": True},
        },
        expected_outputs=[],
        trust_level="experimental",
        trust_notes="Backed by desktop benchmark inspect_folder_basic.",
        created_at=now,
        updated_at=now,
        version="1",
    )
    return save_job_pack(job, repo_root)


def seed_task_demo_job_pack(repo_root: Path | str | None = None) -> Path:
    """Create job pack that references task_demo cli_demo (simulate-only)."""
    now = utc_now_iso()
    job = JobPack(
        job_pack_id="replay_cli_demo",
        title="Replay CLI demo task",
        description="Replay the cli_demo task in simulate mode.",
        category="demo",
        source=JobPackSource(kind="task_demo", ref="cli_demo"),
        required_adapters=["file_ops"],
        required_approvals=[],
        simulate_support=True,
        real_mode_eligibility=False,
        parameter_schema={},
        trust_level="simulate_only",
        trust_notes="Task replay is simulate-only.",
        created_at=now,
        updated_at=now,
        version="1",
    )
    return save_job_pack(job, repo_root)

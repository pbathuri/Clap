"""
Progress tracking for setup sessions.

Updates and persists SetupProgress; used by SetupManager to report status.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.setup.setup_models import SetupProgress, SetupStage
from workflow_dataset.setup.job_store import load_progress, save_progress
from workflow_dataset.utils.dates import utc_now_iso


def update_progress(
    base_dir: Path,
    session_id: str,
    *,
    current_stage: SetupStage | None = None,
    files_scanned: int | None = None,
    artifacts_classified: int | None = None,
    docs_parsed: int | None = None,
    projects_detected: int | None = None,
    style_patterns_extracted: int | None = None,
    graph_nodes_created: int | None = None,
    adapter_errors: int | None = None,
    adapter_skips: int | None = None,
    job_counts: dict[str, int] | None = None,
    details: dict[str, Any] | None = None,
    increment: bool = False,
) -> SetupProgress:
    """
    Load current progress, apply updates (replace or increment), save and return.
    If increment is True, numeric fields are added to existing values; otherwise they replace.
    """
    base_dir = Path(base_dir)
    current = load_progress(base_dir, session_id)
    if current is None:
        current = SetupProgress(
            session_id=session_id,
            updated_utc=utc_now_iso(),
            current_stage=SetupStage.BOOTSTRAP,
        )
    current.updated_utc = utc_now_iso()
    if current_stage is not None:
        current.current_stage = current_stage
    if files_scanned is not None:
        current.files_scanned = (current.files_scanned + files_scanned) if increment else files_scanned
    if artifacts_classified is not None:
        current.artifacts_classified = (current.artifacts_classified + artifacts_classified) if increment else artifacts_classified
    if docs_parsed is not None:
        current.docs_parsed = (current.docs_parsed + docs_parsed) if increment else docs_parsed
    if projects_detected is not None:
        current.projects_detected = (current.projects_detected + projects_detected) if increment else projects_detected
    if style_patterns_extracted is not None:
        current.style_patterns_extracted = (current.style_patterns_extracted + style_patterns_extracted) if increment else style_patterns_extracted
    if graph_nodes_created is not None:
        current.graph_nodes_created = (current.graph_nodes_created + graph_nodes_created) if increment else graph_nodes_created
    if adapter_errors is not None:
        current.adapter_errors = (current.adapter_errors + adapter_errors) if increment else adapter_errors
    if adapter_skips is not None:
        current.adapter_skips = (current.adapter_skips + adapter_skips) if increment else adapter_skips
    if job_counts is not None:
        current.job_counts = job_counts
    if details is not None:
        current.details = {**current.details, **details}
    save_progress(base_dir, current)
    return current


def get_progress(base_dir: Path, session_id: str) -> SetupProgress | None:
    return load_progress(Path(base_dir), session_id)

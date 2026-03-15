"""
M12: Bridge generated sandbox outputs into the existing apply-plan/apply/rollback workflow.

Does NOT write to real project. Creates adoption candidates and builds apply plan for user confirmation.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.review.review_models import AdoptionCandidate
from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.utils.hashes import stable_id


def _review_root(store_path: Path | str) -> Path:
    p = Path(store_path)
    if not p.is_absolute():
        p = (Path.cwd() / p).resolve()
    return p


def create_adoption_candidate(
    generation_id: str,
    workspace_path: str | Path,
    candidate_paths: list[str],
    artifact_id: str = "",
    target_project_id: str = "",
) -> AdoptionCandidate:
    """Build an AdoptionCandidate for selected generated outputs."""
    workspace_path = Path(workspace_path)
    # Normalize to relative paths if any are absolute under workspace
    rel_paths: list[str] = []
    for c in candidate_paths:
        p = Path(c)
        if p.is_absolute():
            try:
                rel = p.relative_to(workspace_path)
                rel_paths.append(str(rel))
            except ValueError:
                rel_paths.append(c)
        else:
            rel_paths.append(c)
    ts = utc_now_iso()
    adoption_id = stable_id("adopt", generation_id, str(workspace_path), ts, prefix="adopt")
    return AdoptionCandidate(
        adoption_id=adoption_id,
        artifact_id=artifact_id or generation_id,
        generation_id=generation_id,
        workspace_path=str(workspace_path.resolve()),
        candidate_paths=rel_paths,
        target_project_id=target_project_id,
        ready_for_apply=True,
        created_utc=ts,
    )


def save_adoption_candidate(candidate: AdoptionCandidate, store_path: Path | str) -> Path:
    """Persist adoption candidate. Returns path to file."""
    root = _review_root(store_path)
    base = root / "adoptions"
    base.mkdir(parents=True, exist_ok=True)
    path = base / f"{candidate.adoption_id}.json"
    path.write_text(candidate.model_dump_json(indent=2), encoding="utf-8")
    return path


def load_adoption_candidate(adoption_id: str, store_path: Path | str) -> AdoptionCandidate | None:
    """Load adoption candidate by id."""
    root = _review_root(store_path)
    path = root / "adoptions" / f"{adoption_id}.json"
    if not path.exists():
        return None
    return AdoptionCandidate.model_validate_json(path.read_text(encoding="utf-8"))


def build_apply_plan_for_adoption(
    candidate: AdoptionCandidate,
    target_root: str | Path,
    allow_overwrite: bool = False,
) -> tuple[Any | None, str]:
    """
    Build an ApplyPlan from an adoption candidate (generation workspace -> target path).
    Returns (ApplyPlan or None, error_message). Does NOT execute; caller uses existing apply flow.
    """
    from workflow_dataset.apply.copy_planner import build_apply_plan

    ws = Path(candidate.workspace_path).resolve()
    target = Path(target_root).resolve()
    if not ws.exists() or not ws.is_dir():
        return None, "Generation workspace does not exist"
    plan, err = build_apply_plan(
        ws,
        target,
        selected_paths=candidate.candidate_paths or None,
        allow_overwrite=allow_overwrite,
        dry_run=True,
    )
    return plan, err or ""


def list_adoption_candidates(store_path: Path | str, generation_id: str = "") -> list[AdoptionCandidate]:
    """List adoption candidates; optionally filter by generation_id."""
    root = _review_root(store_path)
    base = root / "adoptions"
    if not base.exists():
        return []
    out = []
    for p in base.glob("*.json"):
        try:
            c = AdoptionCandidate.model_validate_json(p.read_text(encoding="utf-8"))
            if not generation_id or c.generation_id == generation_id:
                out.append(c)
        except Exception:
            continue
    return sorted(out, key=lambda x: x.created_utc, reverse=True)

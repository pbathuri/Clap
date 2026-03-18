"""
M24E: Persist recipe runs under data/local/specialization/recipe_runs/. Local-only, inspectable.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from workflow_dataset.specialization.recipe_run_models import RecipeRun, RECIPE_RUN_STATUSES

RUNS_DIR_NAME = "data/local/specialization/recipe_runs"


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd()


def _runs_dir(repo_root: Path | str | None) -> Path:
    return _repo_root(repo_root) / RUNS_DIR_NAME


def _run_path(run_id: str, repo_root: Path | str | None) -> Path:
    return _runs_dir(repo_root) / f"{run_id}.json"


def _run_to_dict(r: RecipeRun) -> dict[str, Any]:
    return {
        "run_id": r.run_id,
        "source_recipe_id": r.source_recipe_id,
        "target_domain_pack_id": r.target_domain_pack_id or "",
        "target_value_pack_id": r.target_value_pack_id or "",
        "target_starter_kit_id": r.target_starter_kit_id or "",
        "machine_assumptions": r.machine_assumptions,
        "approvals_required": list(r.approvals_required),
        "steps_planned": list(r.steps_planned),
        "steps_done": list(r.steps_done),
        "outputs_expected": list(r.outputs_expected),
        "outputs_produced": list(r.outputs_produced),
        "reversible": r.reversible,
        "status": r.status,
        "started_at": r.started_at,
        "finished_at": r.finished_at,
        "rollback_notes": r.rollback_notes or "",
        "error_message": r.error_message or "",
        "dry_run": r.dry_run,
    }


def _dict_to_run(d: dict[str, Any]) -> RecipeRun:
    return RecipeRun(
        run_id=d.get("run_id", ""),
        source_recipe_id=d.get("source_recipe_id", ""),
        target_domain_pack_id=d.get("target_domain_pack_id", ""),
        target_value_pack_id=d.get("target_value_pack_id", ""),
        target_starter_kit_id=d.get("target_starter_kit_id", ""),
        machine_assumptions=d.get("machine_assumptions") or {},
        approvals_required=list(d.get("approvals_required") or []),
        steps_planned=list(d.get("steps_planned") or []),
        steps_done=list(d.get("steps_done") or []),
        outputs_expected=list(d.get("outputs_expected") or []),
        outputs_produced=list(d.get("outputs_produced") or []),
        reversible=d.get("reversible", True),
        status=d.get("status", "pending"),
        started_at=d.get("started_at", ""),
        finished_at=d.get("finished_at", ""),
        rollback_notes=d.get("rollback_notes", ""),
        error_message=d.get("error_message", ""),
        dry_run=d.get("dry_run", False),
    )


def save_run(run: RecipeRun, repo_root: Path | str | None = None) -> Path:
    """Persist a recipe run. Returns path to written file."""
    root = _runs_dir(repo_root)
    root.mkdir(parents=True, exist_ok=True)
    path = _run_path(run.run_id, repo_root)
    path.write_text(json.dumps(_run_to_dict(run), indent=2), encoding="utf-8")
    return path


def get_run(run_id: str, repo_root: Path | str | None = None) -> RecipeRun | None:
    """Load a recipe run by id."""
    path = _run_path(run_id, repo_root)
    if not path.exists() or not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return _dict_to_run(data)
    except Exception:
        return None


def list_runs(repo_root: Path | str | None = None, limit: int = 50) -> list[RecipeRun]:
    """List recipe runs, newest first (by file mtime)."""
    root = _runs_dir(repo_root)
    if not root.exists():
        return []
    files = sorted(root.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    runs: list[RecipeRun] = []
    for p in files[:limit]:
        run_id = p.stem
        r = get_run(run_id, repo_root)
        if r:
            runs.append(r)
    return runs


def generate_run_id(prefix: str = "run") -> str:
    """Generate a unique run id."""
    return f"{prefix}_{int(time.time() * 1000)}"

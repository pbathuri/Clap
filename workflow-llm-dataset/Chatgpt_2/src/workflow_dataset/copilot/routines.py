"""
M23K: Routines / job bundles. Local, inspectable, operator-controlled.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None

from workflow_dataset.copilot.config import get_routines_dir


@dataclass
class Routine:
    """Ordered bundle of job packs with optional stop conditions."""
    routine_id: str
    title: str
    description: str = ""
    job_pack_ids: list[str] = field(default_factory=list)
    ordering: list[int] | None = None  # index into job_pack_ids; if None use 0..n-1
    stop_on_first_blocked: bool = True
    required_approvals: list[str] = field(default_factory=list)
    simulate_only: bool = True  # if True, routine runs only in simulate mode
    expected_outputs: list[str] = field(default_factory=list)


def _routine_to_dict(r: Routine) -> dict[str, Any]:
    return {
        "routine_id": r.routine_id,
        "title": r.title,
        "description": r.description,
        "job_pack_ids": r.job_pack_ids,
        "ordering": r.ordering,
        "stop_on_first_blocked": r.stop_on_first_blocked,
        "required_approvals": r.required_approvals,
        "simulate_only": r.simulate_only,
        "expected_outputs": r.expected_outputs,
    }


def _routine_from_dict(d: dict[str, Any], rid: str = "") -> Routine:
    return Routine(
        routine_id=str(d.get("routine_id", rid)),
        title=str(d.get("title", "")),
        description=str(d.get("description", "")),
        job_pack_ids=list(d.get("job_pack_ids") or []),
        ordering=list(d.get("ordering")) if d.get("ordering") is not None else None,
        stop_on_first_blocked=bool(d.get("stop_on_first_blocked", True)),
        required_approvals=list(d.get("required_approvals") or []),
        simulate_only=bool(d.get("simulate_only", True)),
        expected_outputs=list(d.get("expected_outputs") or []),
    )


def _safe_id(routine_id: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in routine_id.strip())


def _routine_path(routine_id: str, repo_root: Path | str | None) -> Path:
    return get_routines_dir(repo_root) / f"{_safe_id(routine_id)}.yaml"


def list_routines(repo_root: Path | str | None = None) -> list[str]:
    ids = []
    for f in get_routines_dir(repo_root).iterdir():
        if f.is_file() and f.suffix.lower() in (".yaml", ".yml", ".json"):
            ids.append(f.stem)
    return sorted(ids)


def get_routine(routine_id: str, repo_root: Path | str | None = None) -> Routine | None:
    path = _routine_path(routine_id, repo_root)
    if not path.exists() or not path.is_file():
        return None
    raw = path.read_text(encoding="utf-8")
    try:
        if path.suffix.lower() in (".yaml", ".yml") and yaml:
            data = yaml.safe_load(raw) or {}
        else:
            import json
            data = json.loads(raw) or {}
    except Exception:
        return None
    return _routine_from_dict(data, path.stem)


def save_routine(routine: Routine, repo_root: Path | str | None = None) -> Path:
    path = _routine_path(routine.routine_id, repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = _routine_to_dict(routine)
    if yaml:
        path.write_text(yaml.dump(data, default_flow_style=False, allow_unicode=True), encoding="utf-8")
    else:
        import json
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def get_ordered_job_ids(routine: Routine) -> list[str]:
    """Return job_pack_ids in order (using ordering if set)."""
    if routine.ordering is not None:
        out = []
        for i in routine.ordering:
            if 0 <= i < len(routine.job_pack_ids):
                out.append(routine.job_pack_ids[i])
        return out
    return list(routine.job_pack_ids)

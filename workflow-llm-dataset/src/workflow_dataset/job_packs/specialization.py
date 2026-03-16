"""
M23J: Specialization memory per job pack. Local-only; updates only via explicit paths.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()


@dataclass
class SpecializationMemory:
    """Per-job user-specific context: preferred params, paths, last run, notes."""
    job_pack_id: str
    preferred_params: dict[str, Any] = field(default_factory=dict)
    preferred_paths: list[str] = field(default_factory=list)
    preferred_apps: list[str] = field(default_factory=list)
    preferred_output_style: str = ""
    operator_notes: str = ""
    last_successful_run: dict[str, Any] = field(default_factory=dict)  # run_id, timestamp, params_used, outcome
    recurring_failure_notes: list[str] = field(default_factory=list)
    confidence_notes: str = ""
    updated_at: str = ""
    update_history: list[dict[str, Any]] = field(default_factory=list)  # [{at, source, summary}]


def _path(repo_root: Path | str | None, job_pack_id: str) -> Path:
    from workflow_dataset.job_packs.config import get_specialization_path
    return get_specialization_path(job_pack_id, repo_root)


def _to_dict(s: SpecializationMemory) -> dict[str, Any]:
    return {
        "job_pack_id": s.job_pack_id,
        "preferred_params": s.preferred_params,
        "preferred_paths": s.preferred_paths,
        "preferred_apps": s.preferred_apps,
        "preferred_output_style": s.preferred_output_style,
        "operator_notes": s.operator_notes,
        "last_successful_run": s.last_successful_run,
        "recurring_failure_notes": s.recurring_failure_notes,
        "confidence_notes": s.confidence_notes,
        "updated_at": s.updated_at,
        "update_history": s.update_history[-50:],  # keep last 50
    }


def _from_dict(d: dict[str, Any], jid: str = "") -> SpecializationMemory:
    return SpecializationMemory(
        job_pack_id=str(d.get("job_pack_id", jid)),
        preferred_params=dict(d.get("preferred_params") or {}),
        preferred_paths=list(d.get("preferred_paths") or []),
        preferred_apps=list(d.get("preferred_apps") or []),
        preferred_output_style=str(d.get("preferred_output_style", "")),
        operator_notes=str(d.get("operator_notes", "")),
        last_successful_run=dict(d.get("last_successful_run") or {}),
        recurring_failure_notes=list(d.get("recurring_failure_notes") or []),
        confidence_notes=str(d.get("confidence_notes", "")),
        updated_at=str(d.get("updated_at", "")),
        update_history=list(d.get("update_history") or []),
    )


def load_specialization(job_pack_id: str, repo_root: Path | str | None = None) -> SpecializationMemory:
    """Load specialization for job; returns empty memory if file missing."""
    path = _path(repo_root, job_pack_id)
    if not path.exists() or not path.is_file():
        return SpecializationMemory(job_pack_id=job_pack_id)
    raw = path.read_text(encoding="utf-8")
    try:
        if path.suffix.lower() in (".yaml", ".yml") and yaml:
            data = yaml.safe_load(raw) or {}
        else:
            import json
            data = json.loads(raw) or {}
    except Exception:
        return SpecializationMemory(job_pack_id=job_pack_id)
    return _from_dict(data, job_pack_id)


def save_specialization(memory: SpecializationMemory, repo_root: Path | str | None = None) -> Path:
    """Persist specialization. Call only from explicit update paths."""
    path = _path(repo_root, memory.job_pack_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    memory.updated_at = utc_now_iso()
    data = _to_dict(memory)
    if yaml:
        path.write_text(yaml.dump(data, default_flow_style=False, allow_unicode=True), encoding="utf-8")
    else:
        import json
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def update_from_successful_run(
    job_pack_id: str,
    run_id: str,
    timestamp: str,
    params_used: dict[str, Any],
    outcome: str = "pass",
    repo_root: Path | str | None = None,
) -> SpecializationMemory:
    """Update specialization from a successful run (operator-confirmed or benchmark pass). Explicit path only."""
    mem = load_specialization(job_pack_id, repo_root)
    mem.last_successful_run = {
        "run_id": run_id,
        "timestamp": timestamp,
        "params_used": params_used,
        "outcome": outcome,
    }
    mem.update_history.append({
        "at": utc_now_iso(),
        "source": "successful_run",
        "summary": f"run_id={run_id} outcome={outcome}",
    })
    save_specialization(mem, repo_root)
    return mem


def update_from_operator_override(
    job_pack_id: str,
    preferred_params: dict[str, Any] | None = None,
    preferred_paths: list[str] | None = None,
    operator_notes: str | None = None,
    repo_root: Path | str | None = None,
) -> SpecializationMemory:
    """Update specialization from operator-confirmed override. Explicit path only."""
    mem = load_specialization(job_pack_id, repo_root)
    if preferred_params is not None:
        mem.preferred_params = dict(preferred_params)
    if preferred_paths is not None:
        mem.preferred_paths = list(preferred_paths)
    if operator_notes is not None:
        mem.operator_notes = operator_notes
    mem.update_history.append({
        "at": utc_now_iso(),
        "source": "operator_override",
        "summary": "params/paths/notes updated",
    })
    save_specialization(mem, repo_root)
    return mem


def save_as_preferred(
    job_pack_id: str,
    params: dict[str, Any],
    repo_root: Path | str | None = None,
) -> SpecializationMemory:
    """Explicit 'save current params as preferred'. Operator action only."""
    mem = load_specialization(job_pack_id, repo_root)
    mem.preferred_params = dict(params)
    mem.update_history.append({
        "at": utc_now_iso(),
        "source": "save_as_preferred",
        "summary": f"params keys: {list(params.keys())}",
    })
    save_specialization(mem, repo_root)
    return mem

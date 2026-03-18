"""
M23J: Job pack schema. Local, inspectable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None


@dataclass
class JobPackSource:
    """Source reference: task_demo, benchmark_case, or chain/template id."""
    kind: str  # "task_demo" | "benchmark_case" | "chain" | "template"
    ref: str   # task_id, benchmark_id, or other id


@dataclass
class JobPack:
    """Reusable personal job pack."""
    job_pack_id: str
    title: str
    description: str = ""
    category: str = ""
    source: JobPackSource | None = None  # task_demo ref or benchmark_case ref
    required_adapters: list[str] = field(default_factory=list)
    required_approvals: list[str] = field(default_factory=list)
    required_capabilities: dict[str, Any] = field(default_factory=dict)
    simulate_support: bool = True
    real_mode_eligibility: bool = False
    parameter_schema: dict[str, Any] = field(default_factory=dict)  # param name -> {type, default, required}
    expected_outputs: list[str] = field(default_factory=list)
    coordination_graph_ref: dict[str, Any] = field(default_factory=dict)
    trust_level: str = "experimental"  # simulate_only | trusted_for_real | approval_required_every_run | approval_valid_for_scope | experimental | benchmark_only
    trust_notes: str = ""
    created_at: str = ""
    updated_at: str = ""
    version: str = "1"


def _source_from_dict(d: dict | None) -> JobPackSource | None:
    if not d or not isinstance(d, dict):
        return None
    kind = str(d.get("kind", ""))
    ref = str(d.get("ref", ""))
    if not kind or not ref:
        return None
    return JobPackSource(kind=kind, ref=ref)


def _source_to_dict(s: JobPackSource | None) -> dict:
    if not s:
        return {}
    return {"kind": s.kind, "ref": s.ref}


def job_pack_to_dict(j: JobPack) -> dict[str, Any]:
    return {
        "job_pack_id": j.job_pack_id,
        "title": j.title,
        "description": j.description,
        "category": j.category,
        "source": _source_to_dict(j.source),
        "required_adapters": j.required_adapters,
        "required_approvals": j.required_approvals,
        "required_capabilities": j.required_capabilities,
        "simulate_support": j.simulate_support,
        "real_mode_eligibility": j.real_mode_eligibility,
        "parameter_schema": j.parameter_schema,
        "expected_outputs": j.expected_outputs,
        "coordination_graph_ref": j.coordination_graph_ref,
        "trust_level": j.trust_level,
        "trust_notes": j.trust_notes,
        "created_at": j.created_at,
        "updated_at": j.updated_at,
        "version": j.version,
    }


def _job_pack_from_dict(d: dict[str, Any], jid: str = "") -> JobPack:
    return JobPack(
        job_pack_id=str(d.get("job_pack_id", jid)),
        title=str(d.get("title", "")),
        description=str(d.get("description", "")),
        category=str(d.get("category", "")),
        source=_source_from_dict(d.get("source")),
        required_adapters=list(d.get("required_adapters") or []),
        required_approvals=list(d.get("required_approvals") or []),
        required_capabilities=dict(d.get("required_capabilities") or {}),
        simulate_support=bool(d.get("simulate_support", True)),
        real_mode_eligibility=bool(d.get("real_mode_eligibility", False)),
        parameter_schema=dict(d.get("parameter_schema") or {}),
        expected_outputs=list(d.get("expected_outputs") or []),
        coordination_graph_ref=dict(d.get("coordination_graph_ref") or {}),
        trust_level=str(d.get("trust_level", "experimental")),
        trust_notes=str(d.get("trust_notes", "")),
        created_at=str(d.get("created_at", "")),
        updated_at=str(d.get("updated_at", "")),
        version=str(d.get("version", "1")),
    )


def load_job_pack(path: Path | str, job_pack_id: str = "") -> JobPack | None:
    """Load job pack from YAML or JSON file."""
    path = Path(path)
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
    jid = job_pack_id or data.get("job_pack_id") or path.stem
    return _job_pack_from_dict(data, jid)


def list_job_packs(repo_root: Path | str | None = None) -> list[str]:
    """List job pack ids (from filenames)."""
    from workflow_dataset.job_packs.config import get_job_packs_root
    root = get_job_packs_root(repo_root)
    ids = []
    for f in root.iterdir():
        if f.is_file() and f.suffix.lower() in (".yaml", ".yml", ".json") and f.name != "runs":
            ids.append(f.stem)
    return sorted(ids)


def get_job_pack(job_pack_id: str, repo_root: Path | str | None = None) -> JobPack | None:
    """Load job pack by id."""
    from workflow_dataset.job_packs.config import get_job_pack_path
    path = get_job_pack_path(job_pack_id, repo_root)
    return load_job_pack(path, job_pack_id)

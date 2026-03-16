"""
M23M: Update preview, apply, reject. Reversible learning records.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

from workflow_dataset.corrections.config import get_updates_dir, get_proposed_dir
from workflow_dataset.corrections.propose import propose_updates, ProposedUpdate


@dataclass
class UpdateRecord:
    """Record of an applied (or reverted) update."""
    update_id: str
    correction_ids: list[str]
    target_type: str
    target_id: str
    before_value: Any
    after_value: Any
    applied_at: str = ""
    reverted_at: str = ""
    reversible: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "update_id": self.update_id,
            "correction_ids": self.correction_ids,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "before_value": self.before_value,
            "after_value": self.after_value,
            "applied_at": self.applied_at,
            "reverted_at": self.reverted_at,
            "reversible": self.reversible,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> UpdateRecord:
        return cls(
            update_id=str(d.get("update_id", "")),
            correction_ids=list(d.get("correction_ids", [])),
            target_type=str(d.get("target_type", "")),
            target_id=str(d.get("target_id", "")),
            before_value=d.get("before_value"),
            after_value=d.get("after_value"),
            applied_at=str(d.get("applied_at", "")),
            reverted_at=str(d.get("reverted_at", "")),
            reversible=bool(d.get("reversible", True)),
        )


def _proposed_path(update_id: str, repo_root: Path | str | None) -> Path:
    return get_proposed_dir(repo_root) / f"{update_id}.json"


def _update_path(update_id: str, repo_root: Path | str | None) -> Path:
    return get_updates_dir(repo_root) / f"{update_id}.json"


def save_proposed(proposed: ProposedUpdate, repo_root: Path | str | None = None) -> Path:
    """Persist a proposed update so it can be previewed/applied later."""
    path = _proposed_path(proposed.update_id, repo_root)
    path.write_text(json.dumps({
        "update_id": proposed.update_id,
        "correction_ids": proposed.correction_ids,
        "target_type": proposed.target_type,
        "target_id": proposed.target_id,
        "before_value": proposed.before_value,
        "after_value": proposed.after_value,
        "risk_level": proposed.risk_level,
        "reversible": proposed.reversible,
        "reason": proposed.reason,
    }, indent=2), encoding="utf-8")
    return path


def load_proposed(update_id: str, repo_root: Path | str | None = None) -> ProposedUpdate | None:
    p = _proposed_path(update_id, repo_root)
    if not p.exists():
        return None
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        return ProposedUpdate(
            update_id=d["update_id"],
            correction_ids=d["correction_ids"],
            target_type=d["target_type"],
            target_id=d["target_id"],
            before_value=d.get("before_value"),
            after_value=d.get("after_value"),
            risk_level=d.get("risk_level", "low"),
            reversible=d.get("reversible", True),
            reason=d.get("reason", ""),
        )
    except Exception:
        return None


def save_update_record(record: UpdateRecord, repo_root: Path | str | None = None) -> Path:
    path = _update_path(record.update_id, repo_root)
    path.write_text(json.dumps(record.to_dict(), indent=2), encoding="utf-8")
    return path


def load_update_record(update_id: str, repo_root: Path | str | None = None) -> UpdateRecord | None:
    path = _update_path(update_id, repo_root)
    if not path.exists():
        return None
    try:
        return UpdateRecord.from_dict(json.loads(path.read_text(encoding="utf-8")))
    except Exception:
        return None


def preview_update(update_id: str, repo_root: Path | str | None = None) -> dict[str, Any]:
    """Return human-readable preview: what would change, before/after, risk."""
    root = Path(repo_root).resolve() if repo_root else None
    prop = load_proposed(update_id, root)
    if not prop:
        return {"error": f"Proposed update not found: {update_id}"}
    return {
        "update_id": prop.update_id,
        "target_type": prop.target_type,
        "target_id": prop.target_id,
        "before_value": prop.before_value,
        "after_value": prop.after_value,
        "risk_level": prop.risk_level,
        "reversible": prop.reversible,
        "reason": prop.reason,
        "correction_ids": prop.correction_ids,
    }


def apply_update(update_id: str, repo_root: Path | str | None = None) -> dict[str, Any]:
    """Apply a proposed update: mutate specialization/job_pack/routine, then record."""
    root = Path(repo_root).resolve() if repo_root else None
    prop = load_proposed(update_id, root)
    if not prop:
        return {"error": f"Proposed update not found: {update_id}"}

    # Perform the actual update
    if prop.target_type == "specialization_params":
        from workflow_dataset.job_packs import load_specialization
        from workflow_dataset.job_packs.specialization import save_specialization
        mem = load_specialization(prop.target_id, root)
        mem.preferred_params = dict(prop.after_value)
        mem.update_history.append({
            "at": utc_now_iso(),
            "source": "correction_apply",
            "summary": f"update_id={update_id} correction_ids={prop.correction_ids}",
        })
        save_specialization(mem, root)
    elif prop.target_type == "specialization_paths":
        from workflow_dataset.job_packs import load_specialization
        from workflow_dataset.job_packs.specialization import save_specialization
        mem = load_specialization(prop.target_id, root)
        mem.preferred_paths = list(prop.after_value) if isinstance(prop.after_value, list) else [prop.after_value]
        mem.update_history.append({
            "at": utc_now_iso(),
            "source": "correction_apply",
            "summary": f"update_id={update_id}",
        })
        save_specialization(mem, root)
    elif prop.target_type == "specialization_output_style":
        from workflow_dataset.job_packs import load_specialization
        from workflow_dataset.job_packs.specialization import save_specialization
        mem = load_specialization(prop.target_id, root)
        mem.preferred_output_style = str(prop.after_value)
        mem.update_history.append({"at": utc_now_iso(), "source": "correction_apply", "summary": f"update_id={update_id}"})
        save_specialization(mem, root)
    elif prop.target_type == "job_pack_trust_notes":
        from workflow_dataset.job_packs import get_job_pack, save_job_pack
        from workflow_dataset.job_packs.schema import JobPack
        job = get_job_pack(prop.target_id, root)
        if job:
            new_notes = str(prop.after_value)
            updated = JobPack(
                job_pack_id=job.job_pack_id,
                title=job.title,
                description=job.description,
                category=job.category,
                source=job.source,
                required_adapters=job.required_adapters,
                required_approvals=job.required_approvals,
                required_capabilities=job.required_capabilities,
                simulate_support=job.simulate_support,
                real_mode_eligibility=job.real_mode_eligibility,
                parameter_schema=job.parameter_schema,
                expected_outputs=job.expected_outputs,
                coordination_graph_ref=job.coordination_graph_ref,
                trust_level=job.trust_level,
                trust_notes=new_notes,
                created_at=job.created_at,
                updated_at=utc_now_iso(),
                version=job.version,
            )
            save_job_pack(updated, root)
    elif prop.target_type == "routine_ordering":
        from workflow_dataset.copilot.routines import get_routine, save_routine
        from workflow_dataset.copilot.routines import Routine
        r = get_routine(prop.target_id, root)
        if r and isinstance(prop.after_value, list):
            updated = Routine(
                routine_id=r.routine_id,
                title=r.title,
                description=r.description,
                job_pack_ids=prop.after_value,
                ordering=None,
                stop_on_first_blocked=r.stop_on_first_blocked,
                required_approvals=r.required_approvals,
                simulate_only=r.simulate_only,
                expected_outputs=r.expected_outputs,
            )
            save_routine(updated, root)
    elif prop.target_type == "trigger_suppression":
        # Store in a small local file; trigger evaluation can read it later
        from workflow_dataset.corrections.config import get_corrections_root
        overrides_path = get_corrections_root(root) / "trigger_suppressions.json"
        overrides = []
        if overrides_path.exists():
            try:
                overrides = json.loads(overrides_path.read_text(encoding="utf-8"))
            except Exception:
                pass
        if not isinstance(overrides, list):
            overrides = []
        overrides.append({
            "job_or_routine_id": prop.target_id,
            "trigger_type": (prop.after_value or {}).get("trigger_type", "unknown"),
            "suppress": True,
            "update_id": update_id,
        })
        overrides_path.write_text(json.dumps(overrides, indent=2), encoding="utf-8")
    else:
        return {"error": f"Unknown target_type: {prop.target_type}"}

    record = UpdateRecord(
        update_id=prop.update_id,
        correction_ids=prop.correction_ids,
        target_type=prop.target_type,
        target_id=prop.target_id,
        before_value=prop.before_value,
        after_value=prop.after_value,
        applied_at=utc_now_iso(),
        reverted_at="",
        reversible=prop.reversible,
    )
    save_update_record(record, root)
    return {"applied": update_id, "target": f"{prop.target_type}:{prop.target_id}"}


def revert_update(update_id: str, repo_root: Path | str | None = None) -> dict[str, Any]:
    """Restore before state and mark update as reverted."""
    root = Path(repo_root).resolve() if repo_root else None
    record = load_update_record(update_id, root)
    if not record:
        return {"error": f"Update record not found: {update_id}"}
    if record.reverted_at:
        return {"error": f"Update already reverted: {update_id}"}

    # Restore before value
    if record.target_type == "specialization_params":
        from workflow_dataset.job_packs import load_specialization
        from workflow_dataset.job_packs.specialization import save_specialization
        mem = load_specialization(record.target_id, root)
        mem.preferred_params = dict(record.before_value or {})
        mem.update_history.append({"at": utc_now_iso(), "source": "correction_revert", "summary": f"update_id={update_id}"})
        save_specialization(mem, root)
    elif record.target_type == "specialization_paths":
        from workflow_dataset.job_packs import load_specialization
        from workflow_dataset.job_packs.specialization import save_specialization
        mem = load_specialization(record.target_id, root)
        mem.preferred_paths = list(record.before_value or [])
        mem.update_history.append({"at": utc_now_iso(), "source": "correction_revert", "summary": f"update_id={update_id}"})
        save_specialization(mem, root)
    elif record.target_type == "specialization_output_style":
        from workflow_dataset.job_packs import load_specialization
        from workflow_dataset.job_packs.specialization import save_specialization
        mem = load_specialization(record.target_id, root)
        mem.preferred_output_style = str(record.before_value or "")
        mem.update_history.append({"at": utc_now_iso(), "source": "correction_revert", "summary": f"update_id={update_id}"})
        save_specialization(mem, root)
    elif record.target_type == "job_pack_trust_notes":
        from workflow_dataset.job_packs import get_job_pack, save_job_pack
        from workflow_dataset.job_packs.schema import JobPack
        job = get_job_pack(record.target_id, root)
        if job:
            updated = JobPack(
                job_pack_id=job.job_pack_id,
                title=job.title,
                description=job.description,
                category=job.category,
                source=job.source,
                required_adapters=job.required_adapters,
                required_approvals=job.required_approvals,
                required_capabilities=job.required_capabilities,
                simulate_support=job.simulate_support,
                real_mode_eligibility=job.real_mode_eligibility,
                parameter_schema=job.parameter_schema,
                expected_outputs=job.expected_outputs,
                coordination_graph_ref=job.coordination_graph_ref,
                trust_level=job.trust_level,
                trust_notes=str(record.before_value or ""),
                created_at=job.created_at,
                updated_at=utc_now_iso(),
                version=job.version,
            )
            save_job_pack(updated, root)
    elif record.target_type == "routine_ordering":
        from workflow_dataset.copilot.routines import get_routine, save_routine, Routine
        r = get_routine(record.target_id, root)
        if r:
            updated = Routine(
                routine_id=r.routine_id,
                title=r.title,
                description=r.description,
                job_pack_ids=list(record.before_value or []),
                ordering=None,
                stop_on_first_blocked=r.stop_on_first_blocked,
                required_approvals=r.required_approvals,
                simulate_only=r.simulate_only,
                expected_outputs=r.expected_outputs,
            )
            save_routine(updated, root)
    elif record.target_type == "trigger_suppression":
        from workflow_dataset.corrections.config import get_corrections_root
        overrides_path = get_corrections_root(root) / "trigger_suppressions.json"
        if overrides_path.exists():
            try:
                overrides = json.loads(overrides_path.read_text(encoding="utf-8"))
                overrides = [o for o in overrides if o.get("update_id") != update_id]
                overrides_path.write_text(json.dumps(overrides, indent=2), encoding="utf-8")
            except Exception:
                pass

    record.reverted_at = utc_now_iso()
    save_update_record(record, root)
    return {"reverted": update_id, "target": f"{record.target_type}:{record.target_id}"}


def list_proposed_updates(repo_root: Path | str | None = None) -> list[ProposedUpdate]:
    """Return list of proposed updates (from propose_updates and persisted)."""
    proposed = propose_updates(repo_root)
    root = Path(repo_root).resolve() if repo_root else None
    for p in proposed:
        save_proposed(p, root)
    return proposed
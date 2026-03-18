"""
M23M: Propose updates from eligible corrections. No apply yet.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from workflow_dataset.utils.hashes import stable_id
except Exception:
    def stable_id(*parts: str, prefix: str = "") -> str:
        import hashlib
        return prefix + hashlib.sha256("".join(str(p) for p in parts).encode()).hexdigest()[:16]

from workflow_dataset.corrections.store import list_corrections
from workflow_dataset.corrections.rules import get_targets_for_category, LEARNING_RULES


@dataclass
class ProposedUpdate:
    """A single proposed update derived from one or more corrections."""
    update_id: str
    correction_ids: list[str]
    target_type: str
    target_id: str  # job_pack_id, routine_id, etc.
    before_value: Any
    after_value: Any
    risk_level: str
    reversible: bool
    reason: str


def propose_updates(
    repo_root: Path | str | None = None,
    limit_corrections: int = 100,
) -> list[ProposedUpdate]:
    """
    Scan recent eligible corrections and build proposed updates per learning rules.
    Does not apply anything.
    """
    root = Path(repo_root).resolve() if repo_root else None
    corrections = list_corrections(limit=limit_corrections, repo_root=root, eligible_only=True)
    proposed: list[ProposedUpdate] = []
    seen_target: set[tuple[str, str]] = set()  # (target_type, target_id) to avoid dupes

    for c in corrections:
        targets = get_targets_for_category(c.correction_category)
        for target_type in targets:
            rule = LEARNING_RULES.get(target_type)
            if not rule:
                continue
            if c.correction_category not in rule["categories"]:
                continue

            target_id = _target_id_from_correction(c, target_type)
            if not target_id:
                continue
            key = (target_type, target_id)
            if key in seen_target:
                continue
            seen_target.add(key)

            after = _after_value_from_correction(c, target_type)
            before = _before_value_for_target(target_type, target_id, root)
            if after is None:
                continue

            update_id = f"upd_{stable_id(target_type, target_id, c.correction_id, prefix='')[:16]}"
            proposed.append(ProposedUpdate(
                update_id=update_id,
                correction_ids=[c.correction_id],
                target_type=target_type,
                target_id=target_id,
                before_value=before,
                after_value=after,
                risk_level=rule.get("risk", "low"),
                reversible=True,
                reason=f"From correction {c.correction_id}: {c.correction_category}",
            ))
    return proposed


def _target_id_from_correction(c, target_type: str) -> str | None:
    """Infer target_id (job_pack_id, routine_id) from correction source."""
    ref = (c.source_reference_id or "").strip()
    if c.source_type == "job_run":
        return ref or None
    if c.source_type == "recommendation":
        if ref.startswith("rec_"):
            parts = ref.split("_")
            if len(parts) >= 3:
                return "_".join(parts[1:-1])
            return None
        return ref
    if c.source_type == "routine":
        return ref or None
    if target_type == "trigger_suppression":
        return ref or None
    return ref or None


def _after_value_from_correction(c, target_type: str) -> Any:
    if target_type == "specialization_params":
        if isinstance(c.corrected_value, dict):
            return c.corrected_value
        return None
    if target_type == "specialization_paths":
        if isinstance(c.corrected_value, list):
            return c.corrected_value
        if isinstance(c.corrected_value, str):
            return [c.corrected_value]
        return None
    if target_type == "specialization_output_style":
        return c.corrected_value if isinstance(c.corrected_value, str) else str(c.corrected_value or "")
    if target_type == "job_pack_trust_notes":
        return c.corrected_value if isinstance(c.corrected_value, str) else (c.correction_reason or c.notes)
    if target_type == "routine_ordering":
        if isinstance(c.corrected_value, list):
            return c.corrected_value
        return None
    if target_type == "trigger_suppression":
        return {"trigger_type": c.notes or "unknown", "suppress": True}
    return None


def _before_value_for_target(target_type: str, target_id: str, root: Path | None) -> Any:
    """Load current value for target so we can show before/after and revert."""
    if not root:
        return None
    if target_type in ("specialization_params", "specialization_paths", "specialization_output_style"):
        try:
            from workflow_dataset.job_packs import load_specialization
            spec = load_specialization(target_id, root)
            if target_type == "specialization_params":
                return dict(spec.preferred_params)
            if target_type == "specialization_paths":
                return list(spec.preferred_paths)
            if target_type == "specialization_output_style":
                return spec.preferred_output_style
        except Exception:
            return None
    if target_type == "job_pack_trust_notes":
        try:
            from workflow_dataset.job_packs import get_job_pack
            job = get_job_pack(target_id, root)
            return job.trust_notes if job else ""
        except Exception:
            return ""
    if target_type == "routine_ordering":
        try:
            from workflow_dataset.copilot.routines import get_routine
            r = get_routine(target_id, root)
            return list(r.job_pack_ids) if r else []
        except Exception:
            return []
    if target_type == "trigger_suppression":
        return {}
    return None

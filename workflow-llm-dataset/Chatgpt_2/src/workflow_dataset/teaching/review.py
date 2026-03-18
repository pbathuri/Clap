"""
M26I–M26L: Teaching studio review — list candidates, accept/reject, attach to pack.
"""

from __future__ import annotations

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

from workflow_dataset.teaching.skill_models import Skill
from workflow_dataset.teaching.skill_store import load_skill, save_skill, list_skills


def list_candidate_skills(
    status: str = "draft",
    repo_root=None,
    limit: int = 50,
) -> list[Skill]:
    """List skills in draft (or other status) for review."""
    return list_skills(status=status, repo_root=repo_root, limit=limit)


def accept_skill(
    skill_id: str,
    operator_notes: str = "",
    simulate_only_or_trusted_real: str = "simulate_only",
    repo_root=None,
) -> Skill | None:
    """Mark skill as accepted; set simulate_only_or_trusted_real. Does not auto-execute."""
    skill = load_skill(skill_id, repo_root)
    if not skill:
        return None
    skill.status = "accepted"
    skill.accepted_at = utc_now_iso()
    skill.updated_at = skill.accepted_at
    if operator_notes:
        skill.operator_notes = operator_notes
    if simulate_only_or_trusted_real in ("simulate_only", "trusted_real_candidate"):
        skill.simulate_only_or_trusted_real = simulate_only_or_trusted_real
        skill.trust_readiness_status = simulate_only_or_trusted_real
    save_skill(skill, repo_root)
    return skill


def reject_skill(
    skill_id: str,
    operator_notes: str = "",
    repo_root=None,
) -> Skill | None:
    """Mark skill as rejected."""
    skill = load_skill(skill_id, repo_root)
    if not skill:
        return None
    skill.status = "rejected"
    skill.rejected_at = utc_now_iso()
    skill.updated_at = skill.rejected_at
    if operator_notes:
        skill.operator_notes = operator_notes
    save_skill(skill, repo_root)
    return skill


def attach_skill_to_pack(
    skill_id: str,
    pack_id: str,
    repo_root=None,
) -> Skill | None:
    """Add pack to skill's pack_associations (deduplicated)."""
    skill = load_skill(skill_id, repo_root)
    if not skill:
        return None
    if pack_id and pack_id not in skill.pack_associations:
        skill.pack_associations = list(skill.pack_associations) + [pack_id]
    skill.updated_at = utc_now_iso()
    save_skill(skill, repo_root)
    return skill

"""
M26I–M26L: Demo/correction/session → skill draft normalization.
"""

from __future__ import annotations

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

try:
    from workflow_dataset.utils.hashes import stable_id
except Exception:
    def stable_id(*parts: str, prefix: str = "") -> str:
        import hashlib
        return prefix + hashlib.sha256("".join(str(p) for p in parts).encode()).hexdigest()[:16]

from workflow_dataset.teaching.skill_models import Skill
from workflow_dataset.teaching.skill_store import save_skill


def _now() -> str:
    return utc_now_iso()


def demo_to_skill_draft(
    task_id: str,
    goal_family: str = "",
    task_family: str = "",
    repo_root=None,
) -> Skill | None:
    """Convert a task demo to a draft skill. Does not auto-accept."""
    try:
        from workflow_dataset.task_demos.store import get_task
        from workflow_dataset.path_utils import get_repo_root
        root = repo_root if repo_root is not None else get_repo_root()
        task = get_task(task_id, root)
    except Exception:
        return None
    if not task:
        return None
    skill_id = f"skill_demo_{task_id}_{stable_id(task_id, _now(), prefix='')}"
    normalized_steps = []
    for s in task.steps:
        normalized_steps.append({
            "adapter_id": getattr(s, "adapter_id", ""),
            "action_id": getattr(s, "action_id", ""),
            "params": getattr(s, "params", {}) or {},
            "notes": getattr(s, "notes", "") or "",
        })
    skill = Skill(
        skill_id=skill_id,
        source_type="task_demo",
        source_reference_id=task_id,
        goal_family=goal_family or "",
        task_family=task_family or task_id,
        required_capabilities=[],
        required_approvals=[],
        pack_associations=[],
        job_associations=[],
        expected_inputs=[],
        expected_outputs=[],
        trust_readiness_status="unset",
        operator_notes="",
        certification_notes="",
        status="draft",
        simulate_only_or_trusted_real="simulate_only",
        normalized_steps=normalized_steps,
        created_at=_now(),
        updated_at=_now(),
    )
    save_skill(skill, repo_root)
    return skill


def correction_to_skill_draft(
    correction_id: str,
    goal_family: str = "",
    task_family: str = "",
    repo_root=None,
) -> Skill | None:
    """Convert an operator correction to a draft skill (e.g. parameter/style fix). Does not auto-accept."""
    try:
        from workflow_dataset.corrections.store import get_correction
        from workflow_dataset.path_utils import get_repo_root
        root = repo_root if repo_root is not None else get_repo_root()
        ev = get_correction(correction_id, root)
    except Exception:
        return None
    if not ev:
        return None
    skill_id = f"skill_correction_{correction_id}_{stable_id(correction_id, _now(), prefix='')}"
    normalized_steps = [{
        "kind": "correction",
        "category": getattr(ev, "correction_category", ""),
        "original_value": getattr(ev, "original_value", None),
        "corrected_value": getattr(ev, "corrected_value", None),
        "reason": getattr(ev, "correction_reason", ""),
    }]
    skill = Skill(
        skill_id=skill_id,
        source_type="correction",
        source_reference_id=correction_id,
        goal_family=goal_family or "",
        task_family=task_family or getattr(ev, "correction_category", ""),
        required_capabilities=[],
        required_approvals=[],
        pack_associations=[],
        job_associations=[],
        expected_inputs=[],
        expected_outputs=[],
        trust_readiness_status="unset",
        operator_notes=getattr(ev, "notes", "") or "",
        certification_notes="",
        status="draft",
        simulate_only_or_trusted_real="simulate_only",
        normalized_steps=normalized_steps,
        created_at=_now(),
        updated_at=_now(),
    )
    save_skill(skill, repo_root)
    return skill


def manual_skill_draft(
    skill_id: str,
    goal_family: str = "",
    task_family: str = "",
    normalized_steps: list[dict] | None = None,
    expected_inputs: list[str] | None = None,
    expected_outputs: list[str] | None = None,
    operator_notes: str = "",
    repo_root=None,
) -> Skill:
    """Create a manually authored draft skill."""
    skill = Skill(
        skill_id=skill_id,
        source_type="manual",
        source_reference_id="",
        goal_family=goal_family or "",
        task_family=task_family or "",
        required_capabilities=[],
        required_approvals=[],
        pack_associations=[],
        job_associations=[],
        expected_inputs=list(expected_inputs or []),
        expected_outputs=list(expected_outputs or []),
        trust_readiness_status="unset",
        operator_notes=operator_notes or "",
        certification_notes="",
        status="draft",
        simulate_only_or_trusted_real="simulate_only",
        normalized_steps=list(normalized_steps or []),
        created_at=_now(),
        updated_at=_now(),
    )
    save_skill(skill, repo_root)
    return skill

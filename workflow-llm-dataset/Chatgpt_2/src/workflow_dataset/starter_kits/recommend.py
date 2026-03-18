"""
M23Y: Recommend starter kit from profile; compute missing prerequisites.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.starter_kits.models import StarterKit
from workflow_dataset.starter_kits.registry import get_kit, list_kits, BUILTIN_STARTER_KITS

# Map domain_pack_id -> kit_id for recommendation
DOMAIN_PACK_TO_KIT: dict[str, str] = {
    "founder_ops": "founder_ops_starter",
    "office_admin": "founder_ops_starter",
    "research_analyst": "analyst_starter",
    "coding_development": "developer_starter",
    "document_knowledge_worker": "document_worker_starter",
    "logistics_ops": "founder_ops_starter",
    "multilingual": "founder_ops_starter",
    "document_ocr_heavy": "document_worker_starter",
}


def _get_profile_dict(profile: Any) -> dict[str, Any]:
    if profile is None:
        return {}
    if hasattr(profile, "field"):
        return {
            "field": getattr(profile, "field", "") or "",
            "job_family": getattr(profile, "job_family", "") or "",
            "daily_task_style": getattr(profile, "daily_task_style", "") or "",
        }
    if isinstance(profile, dict):
        return {
            "field": profile.get("field", "") or "",
            "job_family": profile.get("job_family", "") or "",
            "daily_task_style": profile.get("daily_task_style", "") or "",
        }
    return {}


def _score_kit_for_profile(kit: StarterKit, field: str, job_family: str, daily_task_style: str) -> float:
    """Score kit match to profile. 0..1."""
    score = 0.0
    field_lower = (field or "").strip().lower()
    job_lower = (job_family or "").strip().lower()
    task_lower = (daily_task_style or "").strip().lower()
    if field_lower and field_lower in (kit.target_field or "").lower():
        score += 0.4
    if job_lower and job_lower in (kit.target_job_family or "").lower():
        score += 0.4
    if task_lower and "code" in task_lower and "developer" in kit.target_job_family.lower():
        score += 0.2
    if task_lower and "document" in task_lower and "document" in kit.kit_id:
        score += 0.2
    if score <= 0.0:
        score = 0.05  # minimal so we can still return first kit as fallback
    return min(1.0, score)


def _missing_prerequisites(kit: StarterKit, repo_root: Path | None) -> list[str]:
    """Return list of missing prerequisites for this kit (jobs/routines not present, approval registry if needed)."""
    missing: list[str] = []
    root = repo_root or Path.cwd()
    try:
        from workflow_dataset.job_packs import get_job_pack, list_job_packs
        existing_jobs = set(list_job_packs(root))
        for jid in kit.recommended_job_ids:
            if jid and jid not in existing_jobs and get_job_pack(jid, root) is None:
                missing.append(f"Job pack not found: {jid} (run jobs seed or create data/local/job_packs/{jid}.yaml)")
    except Exception:
        pass
    try:
        from workflow_dataset.copilot.routines import list_routines, get_routine
        existing_routines = set(list_routines(root))
        for rid in kit.recommended_routine_ids:
            if rid and rid not in existing_routines and get_routine(rid, root) is None:
                missing.append(f"Routine not found: {rid} (add data/local/copilot/routines/{rid}.yaml)")
    except Exception:
        pass
    if kit.first_simulate_only_workflow:
        try:
            from workflow_dataset.copilot.routines import get_routine
            from workflow_dataset.job_packs import get_job_pack
            r = get_routine(kit.first_simulate_only_workflow, root)
            j = get_job_pack(kit.first_simulate_only_workflow, root)
            if r is None and j is None:
                missing.append(f"First workflow '{kit.first_simulate_only_workflow}' not found (routine or job)")
        except Exception:
            pass
    try:
        from workflow_dataset.capability_discovery.approval_registry import get_registry_path
        reg_path = get_registry_path(root)
        if kit.approvals_likely_needed and (not reg_path.exists() or not reg_path.is_file()):
            missing.append("Approval registry missing (data/local/capability_discovery/approvals.yaml); required for real mode.")
    except Exception:
        pass
    return missing


def recommend_kit_from_profile(
    profile: Any = None,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Recommend starter kit from user profile. If profile is None, load from data/local/onboarding/user_work_profile.yaml.
    Returns: kit (StarterKit or None), score, reason, alternatives (list of (StarterKit, score)), missing_prerequisites (list).
    """
    root = Path(repo_root).resolve() if repo_root else None
    if profile is None and root:
        try:
            from workflow_dataset.onboarding.user_work_profile import load_user_work_profile
            loaded = load_user_work_profile(root)
            profile = _get_profile_dict(loaded) if loaded else {}
        except Exception:
            profile = {}
    elif profile is not None:
        profile = _get_profile_dict(profile)
    else:
        profile = {}

    field = profile.get("field", "") or ""
    job_family = profile.get("job_family", "") or ""
    daily_task_style = profile.get("daily_task_style", "") or ""

    # Try domain-pack recommendation first to get primary kit
    primary_kit: StarterKit | None = None
    primary_score = 0.0
    reason = "No profile or match; showing default."
    try:
        from workflow_dataset.domain_packs.registry import recommend_domain_packs
        recs = recommend_domain_packs(field=field, job_family=job_family, daily_task_style=daily_task_style)
        if recs and recs[0][1] > 0.1:
            domain_id = recs[0][0].domain_id
            kit_id = DOMAIN_PACK_TO_KIT.get(domain_id)
            if kit_id:
                primary_kit = get_kit(kit_id)
                primary_score = float(recs[0][1])
                reason = f"Profile (field={field!r}, job_family={job_family!r}) matches domain pack {domain_id} -> kit {kit_id}."
            else:
                primary_kit = get_kit("founder_ops_starter")
                primary_score = 0.3
                reason = f"Domain pack {domain_id} has no dedicated kit; defaulting to founder_ops_starter."
        else:
            primary_kit = get_kit("founder_ops_starter")
            primary_score = 0.2
            reason = "No strong domain match; default founder/operator kit."
    except Exception as e:
        primary_kit = get_kit("founder_ops_starter")
        primary_score = 0.1
        reason = f"Domain recommendation failed ({e}); default kit."

    if primary_kit is None:
        primary_kit = BUILTIN_STARTER_KITS[0] if BUILTIN_STARTER_KITS else None
        primary_score = 0.1

    # Score all kits for alternatives
    scored: list[tuple[StarterKit, float]] = []
    for k in BUILTIN_STARTER_KITS:
        s = _score_kit_for_profile(k, field, job_family, daily_task_style)
        scored.append((k, s))
    scored.sort(key=lambda x: -x[1])
    alternatives = [(k, s) for k, s in scored if k.kit_id != (primary_kit.kit_id if primary_kit else "")][:5]

    missing: list[str] = []
    if primary_kit:
        missing = _missing_prerequisites(primary_kit, root)

    return {
        "kit": primary_kit,
        "score": primary_score,
        "reason": reason,
        "alternatives": alternatives,
        "missing_prerequisites": missing,
    }

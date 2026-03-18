"""
M24B: Recommend value pack from profile; missing prerequisites and simulate-only summary.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.value_packs.models import ValuePack
from workflow_dataset.value_packs.registry import get_value_pack, BUILTIN_VALUE_PACKS

# Map starter_kit_id -> value_pack_id for recommendation
STARTER_KIT_TO_VALUE_PACK: dict[str, str] = {
    "founder_ops_starter": "founder_ops_plus",
    "analyst_starter": "analyst_research_plus",
    "developer_starter": "developer_plus",
    "document_worker_starter": "document_worker_plus",
}


def _get_profile_dict(profile: Any) -> dict[str, Any]:
    if profile is None:
        return {}
    if hasattr(profile, "field"):
        return {"field": getattr(profile, "field", "") or "", "job_family": getattr(profile, "job_family", "") or "", "daily_task_style": getattr(profile, "daily_task_style", "") or ""}
    if isinstance(profile, dict):
        return {"field": profile.get("field", "") or "", "job_family": profile.get("job_family", "") or "", "daily_task_style": profile.get("daily_task_style", "") or ""}
    return {}


def _score_pack_for_profile(pack: ValuePack, field: str, job_family: str) -> float:
    score = 0.0
    fl = (field or "").strip().lower()
    jl = (job_family or "").strip().lower()
    if fl and fl in (pack.target_field or "").lower():
        score += 0.5
    if jl and jl in (pack.target_job_family or "").lower():
        score += 0.5
    if score <= 0.0:
        score = 0.05
    return min(1.0, score)


def _missing_prerequisites(pack: ValuePack, repo_root: Path | None) -> list[str]:
    missing: list[str] = []
    root = repo_root or Path.cwd()
    try:
        from workflow_dataset.job_packs import list_job_packs, get_job_pack
        existing = set(list_job_packs(root))
        for jid in pack.recommended_job_ids:
            if jid and jid not in existing and get_job_pack(jid, root) is None:
                missing.append(f"Job pack not found: {jid}")
    except Exception:
        pass
    try:
        from workflow_dataset.copilot.routines import list_routines, get_routine
        existing = set(list_routines(root))
        for rid in pack.recommended_routine_ids:
            if rid and rid not in existing and get_routine(rid, root) is None:
                missing.append(f"Routine not found: {rid}")
    except Exception:
        pass
    try:
        from workflow_dataset.capability_discovery.approval_registry import get_registry_path
        rp = get_registry_path(root)
        if pack.approvals_likely_needed and (not rp.exists() or not rp.is_file()):
            missing.append("Approval registry missing (data/local/capability_discovery/approvals.yaml); required for real mode.")
    except Exception:
        pass
    return missing


def recommend_value_pack(
    profile: Any = None,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Recommend value pack from profile. Uses starter kit recommendation when available; else scores packs.
    Returns: pack, score, reason, alternatives, missing_prerequisites, simulate_only_summary.
    """
    root = Path(repo_root).resolve() if repo_root else None
    if profile is None and root:
        try:
            from workflow_dataset.onboarding.user_work_profile import load_user_work_profile
            loaded = load_user_work_profile(root)
            profile = _get_profile_dict(loaded) if loaded else {}
        except Exception:
            profile = {}
    else:
        profile = _get_profile_dict(profile) if profile is not None else {}

    field = profile.get("field", "") or ""
    job_family = profile.get("job_family", "") or ""
    primary: ValuePack | None = None
    score = 0.1
    reason = "No profile match; defaulting to founder/operator pack."

    try:
        from workflow_dataset.starter_kits.recommend import recommend_kit_from_profile
        rec = recommend_kit_from_profile(profile=profile, repo_root=root)
        sk = rec.get("kit")
        if sk and sk.kit_id and STARTER_KIT_TO_VALUE_PACK.get(sk.kit_id):
            vp_id = STARTER_KIT_TO_VALUE_PACK[sk.kit_id]
            primary = get_value_pack(vp_id)
            score = float(rec.get("score", 0.2))
            reason = rec.get("reason", reason)
        if primary is None:
            primary = get_value_pack("founder_ops_plus")
    except Exception:
        primary = get_value_pack("founder_ops_plus")

    if primary is None:
        primary = BUILTIN_VALUE_PACKS[0] if BUILTIN_VALUE_PACKS else None

    scored: list[tuple[ValuePack, float]] = [(p, _score_pack_for_profile(p, field, job_family)) for p in BUILTIN_VALUE_PACKS]
    scored.sort(key=lambda x: -x[1])
    alternatives = [(p, s) for p, s in scored if p.pack_id != (primary.pack_id if primary else "")][:5]

    missing: list[str] = []
    if primary:
        missing = _missing_prerequisites(primary, root)

    return {
        "pack": primary,
        "score": score,
        "reason": reason,
        "alternatives": alternatives,
        "missing_prerequisites": missing,
        "simulate_only_summary": primary.simulate_only_summary if primary else "",
    }

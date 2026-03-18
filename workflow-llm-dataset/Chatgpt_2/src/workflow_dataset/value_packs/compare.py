"""
M24B: Compare two value packs — prerequisites, overlap, which fits profile, simulate-only.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.value_packs.models import ValuePack
from workflow_dataset.value_packs.registry import get_value_pack
from workflow_dataset.value_packs.recommend import _missing_prerequisites, _score_pack_for_profile, _get_profile_dict


def compare_value_packs(
    pack_id_a: str,
    pack_id_b: str,
    profile: Any = None,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Compare two value packs. Returns: pack_a, pack_b, missing_a, missing_b, overlap_jobs, overlap_routines,
    score_a, score_b, which_fits_better, simulate_only_a, simulate_only_b.
    """
    root = Path(repo_root).resolve() if repo_root else None
    profile_dict = _get_profile_dict(profile) if profile is not None else {}
    if profile is None and root:
        try:
            from workflow_dataset.onboarding.user_work_profile import load_user_work_profile
            loaded = load_user_work_profile(root)
            profile_dict = _get_profile_dict(loaded) if loaded else {}
        except Exception:
            pass
    field = profile_dict.get("field", "") or ""
    job_family = profile_dict.get("job_family", "") or ""

    pack_a = get_value_pack(pack_id_a)
    pack_b = get_value_pack(pack_id_b)
    if not pack_a or not pack_b:
        return {
            "pack_a": pack_a,
            "pack_b": pack_b,
            "error": f"Pack not found: {pack_id_a if not pack_a else pack_id_b}",
        }

    missing_a = _missing_prerequisites(pack_a, root)
    missing_b = _missing_prerequisites(pack_b, root)
    overlap_jobs = list(set(pack_a.recommended_job_ids) & set(pack_b.recommended_job_ids))
    overlap_routines = list(set(pack_a.recommended_routine_ids) & set(pack_b.recommended_routine_ids))
    score_a = _score_pack_for_profile(pack_a, field, job_family)
    score_b = _score_pack_for_profile(pack_b, field, job_family)
    which_fits_better = pack_id_a if score_a >= score_b else pack_id_b

    return {
        "pack_a": pack_a,
        "pack_b": pack_b,
        "missing_prerequisites_a": missing_a,
        "missing_prerequisites_b": missing_b,
        "overlap_jobs": overlap_jobs,
        "overlap_routines": overlap_routines,
        "score_a": score_a,
        "score_b": score_b,
        "which_fits_better": which_fits_better,
        "simulate_only_summary_a": pack_a.simulate_only_summary,
        "simulate_only_summary_b": pack_b.simulate_only_summary,
    }

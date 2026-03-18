"""
M24E: Domain environment summary — what is provisioned, jobs/routines ready, what needs activation, first-value readiness.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.value_packs.registry import get_value_pack
from workflow_dataset.value_packs.recommend import _missing_prerequisites
from workflow_dataset.value_packs.first_run_flow import build_first_run_flow

PROVISIONING_ROOT = "data/local/provisioning"


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd()


def domain_environment_summary(
    pack_id: str,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Generate summary for a value pack: what is provisioned, jobs/routines/macros ready,
    what still needs activation, what remains simulate-only, recommended first-value run.
    pack_id: value pack id (e.g. founder_ops_plus).
    """
    root = _repo_root(repo_root)
    pack = get_value_pack(pack_id)
    if not pack:
        return {
            "pack_id": pack_id,
            "error": f"Value pack not found: {pack_id}",
            "provisioned": False,
            "jobs_ready": [],
            "routines_ready": [],
            "macros_ready": [],
            "needs_activation": [],
            "simulate_only": [],
            "recommended_first_value_run": "",
            "missing_prerequisites": [],
            "first_value_flow_steps": [],
        }
    missing = _missing_prerequisites(pack, root)
    prov_dir = root / PROVISIONING_ROOT / pack_id
    provisioned = (prov_dir / "provisioning_manifest.json").exists() if prov_dir.exists() else False

    jobs_ready: list[str] = []
    routines_ready: list[str] = []
    macros_ready: list[str] = []
    try:
        from workflow_dataset.job_packs import list_job_packs, get_job_pack
        for jid in pack.recommended_job_ids or []:
            if get_job_pack(jid, root) is not None or jid in list_job_packs(root):
                jobs_ready.append(jid)
    except Exception:
        pass
    try:
        from workflow_dataset.copilot.routines import list_routines, get_routine
        for rid in pack.recommended_routine_ids or []:
            if get_routine(rid, root) is not None or rid in list_routines(root):
                routines_ready.append(rid)
    except Exception:
        pass
    try:
        from workflow_dataset.copilot.routines import list_routines as list_routine_ids
        routine_ids = set(list_routine_ids(root))
        for mid in pack.recommended_macro_ids or []:
            if mid in routine_ids:
                macros_ready.append(mid)
    except Exception:
        pass

    needs_activation: list[str] = []
    for j in (pack.recommended_job_ids or []):
        if j not in jobs_ready:
            needs_activation.append(f"job:{j}")
    for r in (pack.recommended_routine_ids or []):
        if r not in routines_ready:
            needs_activation.append(f"routine:{r}")
    for m in (pack.recommended_macro_ids or []):
        if m not in macros_ready:
            needs_activation.append(f"macro:{m}")
    if missing:
        needs_activation.append("approvals_or_registry")

    simulate_only: list[str] = []
    if pack.simulate_only_summary:
        simulate_only.append(pack.simulate_only_summary)
    if missing:
        simulate_only.append("Real mode requires resolving missing prerequisites.")

    flow = build_first_run_flow(pack_id, root)
    first_value_flow_steps = flow.get("steps") or []
    recommended_first_value_run = ""
    for step in first_value_flow_steps:
        if step.get("title") == "First simulate run" or step.get("title") == "First trusted-real candidate":
            recommended_first_value_run = step.get("command", "")
            break
    if not recommended_first_value_run and first_value_flow_steps:
        recommended_first_value_run = first_value_flow_steps[-1].get("command", "") if first_value_flow_steps else ""

    return {
        "pack_id": pack_id,
        "error": "",
        "provisioned": provisioned,
        "jobs_ready": jobs_ready,
        "routines_ready": routines_ready,
        "macros_ready": macros_ready,
        "needs_activation": needs_activation,
        "simulate_only": simulate_only,
        "recommended_first_value_run": recommended_first_value_run,
        "missing_prerequisites": missing,
        "first_value_flow_steps": first_value_flow_steps,
        "pack_name": pack.name,
    }

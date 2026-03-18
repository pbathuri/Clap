"""
M25E–M25H: Pack behavior runtime API — resolve behavior for a job/task and merge prompt assets for use by execution paths.
Explicit, inspectable; does not bypass trust/approval. Callers use returned behavior to build prompts or attach to results.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.packs.behavior_resolver import resolve_behavior_for_task
from workflow_dataset.packs.behavior_models import ResolvedBehavior, PackPromptAsset

# Order for merging prompt assets by kind (system first, then task/workflow, then hints)
_PROMPT_KIND_ORDER = (
    "system_guidance",
    "task_prompt",
    "workflow_prompt",
    "explanation_style_hint",
    "output_framing_hint",
)


def _packs_dir(repo_root: Path | str | None) -> Path | None:
    if repo_root is None:
        return None
    root = Path(repo_root).resolve()
    return root / "data" / "local" / "packs"


def get_resolved_behavior_for_task(
    task_id: str | None = None,
    workflow_id: str | None = None,
    role: str | None = None,
    repo_root: Path | str | None = None,
) -> Any:
    """
    Resolve pack behavior for the given task/workflow. Returns BehaviorResolutionResult.
    Use for runtime when you have a task or workflow scope (e.g. from workflow kind or template).
    """
    packs_dir = _packs_dir(repo_root)
    return resolve_behavior_for_task(
        task_id=task_id,
        workflow_id=workflow_id,
        role=role,
        packs_dir=packs_dir,
    )


def get_resolved_behavior_for_job(
    job_pack_id: str,
    repo_root: Path | str | None = None,
) -> Any:
    """
    Resolve pack behavior for a job. Uses job_pack_id and job.source.ref as task_id when source is task_demo.
    Returns BehaviorResolutionResult; use .resolved for prompt assets and task defaults.
    """
    from workflow_dataset.job_packs import get_job_pack
    root = Path(repo_root).resolve() if repo_root else None
    job = get_job_pack(job_pack_id, root)
    task_id = job_pack_id
    workflow_id: str | None = None
    if job and job.source:
        if getattr(job.source, "kind", "") == "task_demo" and getattr(job.source, "ref", ""):
            task_id = job.source.ref
        # workflow_id could come from job category or a future field
    packs_dir = _packs_dir(root)
    return resolve_behavior_for_task(
        task_id=task_id,
        workflow_id=workflow_id,
        role=None,
        packs_dir=packs_dir,
    )


def merge_pack_prompts_into_instruction(resolved: ResolvedBehavior) -> str:
    """
    Build a single instruction string from resolved prompt_assets for use by runners.
    Order: system_guidance, task_prompt, workflow_prompt, explanation_style_hint, output_framing_hint.
    Each non-empty content is appended with a newline; safe to prepend to existing prompts.
    """
    if not resolved.prompt_assets:
        return ""
    by_kind: dict[str, list[PackPromptAsset]] = {}
    for a in resolved.prompt_assets:
        if a.kind not in by_kind:
            by_kind[a.kind] = []
        by_kind[a.kind].append(a)
    parts: list[str] = []
    for kind in _PROMPT_KIND_ORDER:
        for a in by_kind.get(kind, []):
            if a.content and a.content.strip():
                parts.append(a.content.strip())
    return "\n\n".join(parts) if parts else ""


def get_behavior_summary_for_job(
    job_pack_id: str,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Return a compact summary of resolved behavior for a job (for attaching to run result).
    Includes winning_pack_id, prompt_instruction (merged), task_defaults, retrieval/output profile, why_*.
    Does not run the job; call from run_job after policy check.
    """
    result = get_resolved_behavior_for_job(job_pack_id, repo_root)
    r = result.resolved
    merged = merge_pack_prompts_into_instruction(r)
    return {
        "winning_pack_id": r.winning_pack_id,
        "active_pack_ids": result.active_pack_ids,
        "prompt_instruction": merged[:2000] if merged else "",  # cap for result size
        "prompt_asset_count": len(r.prompt_assets),
        "task_defaults": {
            "preferred_adapter": r.task_defaults.preferred_adapter if r.task_defaults else "",
            "preferred_model_class": r.task_defaults.preferred_model_class if r.task_defaults else "",
            "preferred_output_mode": r.task_defaults.preferred_output_mode if r.task_defaults else "",
        } if r.task_defaults else {},
        "retrieval_profile": r.retrieval_profile,
        "output_profile": r.output_profile,
        "retrieval_profile_source_pack": r.retrieval_profile_source_pack,
        "output_profile_source_pack": r.output_profile_source_pack,
        "why_winning": result.why_winning,
        "why_retrieval_profile": r.why_retrieval_profile,
        "why_output_profile": r.why_output_profile,
        "excluded_pack_ids": r.excluded_pack_ids,
        "conflict_summary": r.conflict_summary,
    }

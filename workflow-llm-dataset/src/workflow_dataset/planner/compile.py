"""
M26B: Compile goal text into an explicit Plan using session, jobs, routines, macros, demos, packs.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

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
        return prefix + hashlib.sha256("".join(parts).encode()).hexdigest()[:16]

from workflow_dataset.planner.schema import (
    Plan,
    PlanStep,
    DependencyEdge,
    Checkpoint,
    ExpectedArtifact,
    BlockedCondition,
    ProvenanceSource,
)
from workflow_dataset.planner.sources import gather_planning_sources
from workflow_dataset.planner.classify import classify_plan_step


def _normalize_goal(goal: str) -> str:
    return re.sub(r"\s+", " ", (goal or "").strip().lower())


def _tokenize(goal: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", _normalize_goal(goal)))


def _score_match(tokens: set[str], title: str, ref: str, extra: str = "") -> int:
    """Simple keyword overlap score. title and ref are lowercased and tokenized."""
    combined = " ".join([(title or ""), (ref or ""), extra]).lower()
    target = set(re.findall(r"[a-z0-9]+", combined))
    return len(tokens & target)


def compile_goal_to_plan(
    goal: str,
    repo_root: Path | str | None = None,
    mode: str = "simulate",
) -> Plan:
    """
    Compile a goal string into a Plan. Uses keyword matching against job titles, routine/macro ids, task ids.
    Session's active jobs/routines/macros are preferred; then recommendations; then all routines/jobs.
    Steps are ordered; edges are sequential; checkpoints and blocked come from job/macro policy.
    """
    root = Path(repo_root).resolve() if repo_root else None
    sources = gather_planning_sources(root)
    tokens = _tokenize(goal or "")
    plan_id = stable_id("plan", goal or "", utc_now_iso(), prefix="")[:24]
    steps: list[PlanStep] = []
    edges: list[DependencyEdge] = []
    checkpoints: list[Checkpoint] = []
    expected_artifacts: list[ExpectedArtifact] = []
    blocked_conditions: list[BlockedCondition] = []
    sources_used: list[str] = []

    session = sources.get("session") or {}
    active_job_ids = set(session.get("active_job_ids") or [])
    active_routine_ids = set(session.get("active_routine_ids") or [])
    active_macro_ids = set(session.get("active_macro_ids") or [])

    # 1) Prefer matching routine/macro (one routine = one macro)
    best_routine_score = -1
    best_routine_id = ""
    for r in sources.get("routines", []):
        rid = r.get("routine_id", "")
        title = r.get("title", "") or rid
        score = _score_match(tokens, title, rid, r.get("description", ""))
        if score > best_routine_score or (score > 0 and rid in active_routine_ids):
            if score > best_routine_score:
                best_routine_score = score
                best_routine_id = rid
            if rid in active_routine_ids and score > 0:
                best_routine_id = rid
                best_routine_score = max(best_routine_score, score)

    if best_routine_id and (best_routine_score > 0 or best_routine_id in active_routine_ids):
        job_ids = next((r.get("job_pack_ids", []) for r in sources.get("routines", []) if r.get("routine_id") == best_routine_id), [])
        try:
            from workflow_dataset.job_packs import get_job_pack
            from workflow_dataset.macros.runner import get_macro_steps
            macro_steps = get_macro_steps(best_routine_id, mode, root)
            for i, ms in enumerate(macro_steps):
                step_index = len(steps)
                job_id = getattr(ms, "job_pack_id", "") or (job_ids[i] if i < len(job_ids) else "")
                prov = ProvenanceSource(kind="job", ref=job_id, label=job_id) if job_id else ProvenanceSource(kind="macro", ref=best_routine_id, label=best_routine_id)
                job = get_job_pack(job_id, root) if job_id else None
                label = (job.title if job else job_id) or f"Step {step_index + 1}"
                blocked_reason = ""
                if getattr(ms, "step_type", "") == "blocked":
                    blocked_reason = "Policy blocks this step"
                ps = PlanStep(
                    step_index=step_index,
                    label=label,
                    step_class=getattr(ms, "step_type", "") or "sandbox_write",
                    trust_level=getattr(ms, "trust_requirement", ""),
                    approval_required=getattr(ms, "approval_requirement", False),
                    checkpoint_before=getattr(ms, "checkpoint_before", False),
                    expected_outputs=list(getattr(ms, "expected_outputs", []) or []),
                    blocked_reason=blocked_reason,
                    provenance=prov,
                )
                ps.step_class = classify_plan_step(ps, root, mode)
                if ps.checkpoint_before:
                    checkpoints.append(Checkpoint(step_index=step_index, label=label))
                if blocked_reason:
                    blocked_conditions.append(BlockedCondition(reason=blocked_reason, step_index=step_index))
                for out in (ps.expected_outputs or []):
                    expected_artifacts.append(ExpectedArtifact(label=out, step_index=step_index))
                steps.append(ps)
                if step_index > 0:
                    edges.append(DependencyEdge(step_index - 1, step_index, "sequence"))
            sources_used.append(f"routine:{best_routine_id}")
        except Exception:
            pass

    # 2) If no routine matched, try job recommendations and job list
    if not steps:
        candidates: list[tuple[int, str, str, dict]] = []
        for rec in sources.get("job_recommendations", []):
            jid = rec.get("job_pack_id", "")
            title = rec.get("title", "") or jid
            score = _score_match(tokens, title, jid)
            if score > 0 or jid in active_job_ids:
                candidates.append((score, jid, "job", rec))
        for jid in sources.get("job_pack_ids", []):
            if any(c[1] == jid for c in candidates):
                continue
            score = _score_match(tokens, jid, jid)
            if score > 0 or jid in active_job_ids:
                candidates.append((score, jid, "job", {"job_pack_id": jid}))
        candidates.sort(key=lambda x: (-x[0], x[1]))
        seen_job = set()
        try:
            from workflow_dataset.job_packs import get_job_pack
            from workflow_dataset.macros.step_classifier import classify_step
            for score, jid, _, rec in candidates[:15]:
                if jid in seen_job:
                    continue
                seen_job.add(jid)
                job = get_job_pack(jid, root)
                if not job:
                    continue
                step_index = len(steps)
                prov = ProvenanceSource(kind="job", ref=jid, label=getattr(job, "title", jid))
                ms = classify_step(jid, mode, root)
                blocked_reason = ""
                if getattr(ms, "step_type", "") == "blocked":
                    blocked_reason = "Job not allowed in current policy"
                ps = PlanStep(
                    step_index=step_index,
                    label=getattr(job, "title", jid),
                    step_class=getattr(ms, "step_type", "") or "sandbox_write",
                    trust_level=getattr(job, "trust_level", ""),
                    approval_required=bool(getattr(job, "required_approvals", None)),
                    expected_outputs=list(getattr(job, "expected_outputs", []) or []),
                    blocked_reason=blocked_reason,
                    provenance=prov,
                )
                ps.step_class = classify_plan_step(ps, root, mode)
                if ps.approval_required:
                    checkpoints.append(Checkpoint(step_index=step_index, label=ps.label, required_approval="approval"))
                if blocked_reason:
                    blocked_conditions.append(BlockedCondition(reason=blocked_reason, step_index=step_index))
                for out in ps.expected_outputs:
                    expected_artifacts.append(ExpectedArtifact(label=out, step_index=step_index))
                steps.append(ps)
                if step_index > 0:
                    edges.append(DependencyEdge(step_index - 1, step_index, "sequence"))
                sources_used.append(f"job:{jid}")
        except Exception:
            pass

    # 3) If still no steps, add a placeholder "reasoning" step
    if not steps:
        steps.append(PlanStep(
            step_index=0,
            label="No matching jobs or routines; refine goal or add session tasks.",
            step_class="reasoning_only",
            provenance=ProvenanceSource(kind="pack", ref="", label="planning"),
        ))
        sources_used.append("planning:no_match")

    return Plan(
        plan_id=plan_id,
        goal_text=goal or "",
        steps=steps,
        edges=edges,
        checkpoints=checkpoints,
        expected_artifacts=expected_artifacts,
        blocked_conditions=blocked_conditions,
        sources_used=list(dict.fromkeys(sources_used)),
        created_at=utc_now_iso(),
    )

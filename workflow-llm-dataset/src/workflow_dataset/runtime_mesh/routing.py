"""
M42B–M42D: Task-aware runtime routing — task families, route explanation, fallback, degraded mode.
M42D.1: Vertical profiles, routing policies, stronger explanation (preferred/allowed/degraded/blocked).
Local-first; no cloud; explicit and inspectable routes.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.runtime_mesh.backend_registry import (
    load_backend_registry,
    get_backend_profile,
    get_backend_status,
)
from workflow_dataset.runtime_mesh.model_catalog import (
    load_model_catalog,
    get_model_info,
)
from workflow_dataset.runtime_mesh.policy import (
    TASK_CLASS_POLICY,
    recommend_for_task_class,
)
from workflow_dataset.runtime_mesh.profiles_and_policies import (
    get_vertical_profile,
    get_routing_policy,
)

# Task families for product tasks (map to task_class / capability where applicable)
TASK_FAMILIES = (
    "planning",
    "summarization",
    "review",
    "suggestion",
    "vertical_workflow",
    "evaluation",
    "council",
    "adaptation_comparison",
)

# Map task_family -> preferred task_class for policy lookup
TASK_FAMILY_TO_CLASS: dict[str, str] = {
    "planning": "plan_run_review",
    "summarization": "desktop_copilot",
    "review": "plan_run_review",
    "suggestion": "desktop_copilot",
    "vertical_workflow": "codebase_task",
    "evaluation": "plan_run_review",
    "council": "plan_run_review",
    "adaptation_comparison": "codebase_task",
}


def _build_route_outcome(
    primary_model_id: str | None,
    primary_backend_id: str | None,
    backend_status: str,
    is_degraded: bool,
    allow_degraded: bool,
    block_when_no_production_safe: bool,
    candidates: list[Any],
    task_family: str,
    vertical_id: str,
    routing_policy_id: str,
) -> tuple[str, str]:
    """M42D.1: Determine route_outcome (preferred/allowed/degraded/blocked) and reason_why."""
    if primary_model_id and backend_status in ("available", "configured") and not is_degraded:
        return ROUTE_OUTCOME_PREFERRED, "Primary model and backend are available; route is preferred."
    if primary_model_id and is_degraded and allow_degraded:
        return ROUTE_OUTCOME_DEGRADED, "Primary backend is missing or unavailable; using degraded fallback or suggestion."
    if primary_model_id and is_degraded and not allow_degraded:
        return ROUTE_OUTCOME_BLOCKED, "Policy does not allow degraded fallback; primary backend is unavailable."
    if not primary_model_id and not candidates:
        if block_when_no_production_safe:
            return ROUTE_OUTCOME_BLOCKED, f"No production-safe model for task_family={task_family}; policy blocks."
        return ROUTE_OUTCOME_BLOCKED, f"No model available for task_family={task_family} (vertical={vertical_id or 'default'}, policy={routing_policy_id or 'balanced'})."
    if not primary_model_id and candidates:
        return ROUTE_OUTCOME_DEGRADED, "No primary route available; backend missing for all candidates. Install or enable backend."
    return ROUTE_OUTCOME_ALLOWED, "Route is allowed under current policy and vertical profile."


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd()


# M42D.1: Route outcome for stronger explanation
ROUTE_OUTCOME_PREFERRED = "preferred"
ROUTE_OUTCOME_ALLOWED = "allowed"
ROUTE_OUTCOME_DEGRADED = "degraded"
ROUTE_OUTCOME_BLOCKED = "blocked"


def route_for_task(
    task_family: str,
    trust_posture: str = "production",  # production | experimental
    require_production_safe: bool = True,
    vertical_id: str = "",
    routing_policy_id: str = "",
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Route a task family to primary model/backend and fallback chain.
    M42D.1: Optional vertical_id and routing_policy_id; returns route_outcome, reason_why, policy_effect.
    """
    root = _repo_root(repo_root)
    catalog = load_model_catalog(root)
    task_class = TASK_FAMILY_TO_CLASS.get(task_family, "desktop_copilot")
    policy_rec = recommend_for_task_class(task_class, root)
    backend_id = policy_rec.get("backend_id")
    backend_status = policy_rec.get("backend_status")
    capability = policy_rec.get("model_class")
    model_ids_from_policy = policy_rec.get("model_ids", [])

    # M42D.1: Apply routing policy
    rp = get_routing_policy(routing_policy_id) if routing_policy_id else get_routing_policy("balanced")
    vp = get_vertical_profile(vertical_id) if vertical_id else get_vertical_profile("default")
    if rp:
        require_production_safe = rp.prefer_production_safe_only
    allow_degraded = rp.allow_degraded_fallback if rp else True
    block_when_no_production_safe = rp.block_when_no_production_safe if rp else False

    # Models that support this task_family and match trust
    candidates = [
        m for m in catalog
        if (task_family in m.task_families or (capability and capability in m.capability_classes))
        and (require_production_safe and m.production_safe or (trust_posture == "experimental" and (rp and rp.allow_experimental_models) and m.experimental_safe))
    ]
    # M42D.1: Filter by vertical profile
    if vp:
        if vp.allowed_task_families and task_family not in vp.allowed_task_families:
            candidates = []
        if vp.allowed_backends and candidates:
            candidates = [m for m in candidates if m.backend_family in vp.allowed_backends]
        if vp.required_production_safe and candidates:
            candidates = [m for m in candidates if m.production_safe]
    # Prefer models that list this task_family explicitly, then by model_ids from policy order
    primary_model_id = None
    for m in candidates:
        if task_family in m.task_families and get_backend_status(m.backend_family, root) in ("available", "configured"):
            primary_model_id = m.model_id
            break
    if not primary_model_id and candidates:
        for mid in model_ids_from_policy:
            m = get_model_info(mid, root)
            if m and any(c.model_id == m.model_id for c in candidates):
                if get_backend_status(m.backend_family, root) in ("available", "configured"):
                    primary_model_id = m.model_id
                    break
    if not primary_model_id and candidates:
        first = candidates[0]
        if get_backend_status(first.backend_family, root) in ("available", "configured"):
            primary_model_id = first.model_id

    primary_backend_id = None
    if primary_model_id:
        entry = get_model_info(primary_model_id, root)
        primary_backend_id = entry.backend_family if entry else backend_id

    # Fallback chain: follow fallback_model_id from primary, then any available model for task family
    fallback_chain: list[str] = []
    seen = {primary_model_id}
    current_id = primary_model_id
    while current_id:
        entry = get_model_info(current_id, root)
        if not entry or not entry.fallback_model_id or entry.fallback_model_id in seen:
            break
        next_id = entry.fallback_model_id
        next_entry = get_model_info(next_id, root)
        if next_entry and get_backend_status(next_entry.backend_family, root) in ("available", "configured"):
            fallback_chain.append(next_id)
            seen.add(next_id)
        current_id = next_id if next_entry else None

    # Degraded: no primary available
    is_degraded = not primary_model_id or (primary_backend_id and get_backend_status(primary_backend_id, root) not in ("available", "configured"))
    degraded_route = None
    if is_degraded and fallback_chain:
        degraded_route = {"model_id": fallback_chain[0], "reason": "Primary unavailable; using first fallback."}
    elif is_degraded:
        # Suggest first candidate by capability even if backend missing
        if candidates:
            degraded_route = {"model_id": candidates[0].model_id, "reason": "Backend missing or unsupported; install or enable backend for this model."}
        else:
            degraded_route = {"model_id": None, "reason": f"No model available for task_family={task_family} with trust={trust_posture}."}

    # M42D.1: Route outcome and reason_why (preferred / allowed / degraded / blocked)
    route_outcome, reason_why = _build_route_outcome(
        primary_model_id=primary_model_id,
        primary_backend_id=primary_backend_id or backend_id,
        backend_status=backend_status,
        is_degraded=is_degraded,
        allow_degraded=allow_degraded,
        block_when_no_production_safe=block_when_no_production_safe,
        candidates=candidates,
        task_family=task_family,
        vertical_id=vertical_id or (vp.vertical_id if vp else ""),
        routing_policy_id=routing_policy_id or (rp.policy_id if rp else ""),
    )
    explanation = (
        f"task_family={task_family} -> task_class={task_class} -> capability={capability}; "
        f"backend_preference={policy_rec.get('reason', '')}; "
        f"primary={primary_model_id or 'none'} backend={primary_backend_id or 'none'} status={backend_status}. "
        f"Outcome: {route_outcome}. {reason_why}"
    )

    return {
        "task_family": task_family,
        "task_class": task_class,
        "primary_model_id": primary_model_id,
        "primary_backend_id": primary_backend_id or backend_id,
        "backend_status": backend_status,
        "fallback_chain": fallback_chain,
        "explanation": explanation,
        "degraded_route": degraded_route,
        "is_degraded": is_degraded,
        "missing": policy_rec.get("missing", []),
        "route_outcome": route_outcome,
        "reason_why": reason_why,
        "vertical_id": vertical_id or (vp.vertical_id if vp else ""),
        "routing_policy_id": routing_policy_id or (rp.policy_id if rp else ""),
    }


def availability_check(repo_root: Path | str | None = None) -> dict[str, Any]:
    """Check runtime availability: backends status, which task families have a valid route, which are degraded."""
    root = _repo_root(repo_root)
    backends = load_backend_registry(root)
    available = [b.backend_id for b in backends if b.status in ("available", "configured")]
    missing = [b.backend_id for b in backends if b.status == "missing"]
    unsupported = [b.backend_id for b in backends if b.status == "unsupported"]

    routes_ok: list[str] = []
    routes_degraded: list[str] = []
    for tf in TASK_FAMILIES:
        r = route_for_task(tf, repo_root=root)
        if r.get("is_degraded"):
            routes_degraded.append(tf)
        else:
            routes_ok.append(tf)

    return {
        "available_backend_ids": available,
        "missing_backend_ids": missing,
        "unsupported_backend_ids": unsupported,
        "task_families_with_route": routes_ok,
        "task_families_degraded": routes_degraded,
    }


def build_fallback_report(repo_root: Path | str | None = None) -> dict[str, Any]:
    """Build a fallback report: per task family primary, fallback chain, degraded status, and recommended actions."""
    root = _repo_root(repo_root)
    avail = availability_check(root)
    report_entries: list[dict[str, Any]] = []
    for tf in TASK_FAMILIES:
        r = route_for_task(tf, repo_root=root)
        report_entries.append({
            "task_family": tf,
            "primary_model_id": r.get("primary_model_id"),
            "primary_backend_id": r.get("primary_backend_id"),
            "backend_status": r.get("backend_status"),
            "fallback_chain": r.get("fallback_chain", []),
            "is_degraded": r.get("is_degraded", False),
            "degraded_route": r.get("degraded_route"),
            "explanation_short": r.get("explanation", "")[:200],
        })

    recommended_actions: list[str] = []
    if avail.get("missing_backend_ids"):
        recommended_actions.append("Install or enable backends: " + ", ".join(avail["missing_backend_ids"][:5]))
    if avail.get("task_families_degraded"):
        recommended_actions.append("Degraded task families (add model or backend): " + ", ".join(avail["task_families_degraded"][:5]))

    return {
        "availability": avail,
        "per_task_family": report_entries,
        "recommended_actions": recommended_actions,
        "summary": f"Routes OK: {len(avail.get('task_families_with_route', []))}; Degraded: {len(avail.get('task_families_degraded', []))}.",
    }


def explain_route(
    task_family: str,
    trust_posture: str = "production",
    vertical_id: str = "",
    routing_policy_id: str = "",
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """Return full route result with explanation for CLI --explain. M42D.1: vertical_id, routing_policy_id."""
    return route_for_task(
        task_family,
        trust_posture=trust_posture,
        vertical_id=vertical_id,
        routing_policy_id=routing_policy_id,
        repo_root=repo_root,
    )

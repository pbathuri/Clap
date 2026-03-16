"""
M23B-F2: Edge deployment tiers.
Local profile categories (dev_full, local_standard, constrained_edge, minimal_eval).
No hardware device specs; explicit tier assumptions for deployer clarity.
"""

from __future__ import annotations

from typing import Any

from workflow_dataset.release.reporting_workspaces import REPORTING_WORKFLOWS

# Tier ids (local profile categories only)
EDGE_TIERS = ("dev_full", "local_standard", "constrained_edge", "minimal_eval")

# Human-readable descriptions
TIER_DESCRIPTIONS: dict[str, str] = {
    "dev_full": "Full dev: all sandbox paths, LLM required, adapter/retrieval optional.",
    "local_standard": "Standard local: core paths and LLM; adapter/retrieval optional.",
    "constrained_edge": "Constrained: minimal paths; LLM optional (baseline only when present).",
    "minimal_eval": "Eval-only: data/local + eval; no reporting workflows.",
}

# Path subsets per tier (all relative to repo root, under data/local)
TIER_REQUIRED_PATHS: dict[str, tuple[str, ...]] = {
    "dev_full": (
        "data/local/workspaces",
        "data/local/packages",
        "data/local/pilot",
        "data/local/review",
        "data/local/staging",
        "data/local/devlab",
        "data/local/eval",
        "data/local/llm/runs",
        "data/local/llm/corpus",
        "data/local/llm/sft",
        "data/local/incubator",
        "data/local/packs",
        "data/local/input_packs",
        "data/local/trials",
    ),
    "local_standard": (
        "data/local/workspaces",
        "data/local/packages",
        "data/local/pilot",
        "data/local/review",
        "data/local/staging",
        "data/local/llm/runs",
        "data/local/packs",
        "data/local/input_packs",
    ),
    "constrained_edge": (
        "data/local",
        "data/local/workspaces",
        "data/local/packages",
    ),
    "minimal_eval": (
        "data/local",
        "data/local/eval",
    ),
}

# LLM requirement per tier: "required" | "optional" | "none"
TIER_LLM_REQUIREMENT: dict[str, str] = {
    "dev_full": "required",
    "local_standard": "required",
    "constrained_edge": "optional",
    "minimal_eval": "none",
}

# Per-workflow status per tier: supported | degraded | unavailable
# reason: short why; missing_functionality: list; fallback: what user can do instead
def _workflow_status(
    workflow: str,
    status: str,
    reason: str,
    missing_functionality: list[str],
    fallback: str | None,
) -> dict[str, Any]:
    return {
        "workflow": workflow,
        "status": status,
        "reason": reason,
        "missing_functionality": missing_functionality,
        "fallback": fallback,
    }


def _all_supported(reason: str = "Full LLM and sandbox available.") -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for wf in REPORTING_WORKFLOWS:
        out[wf] = _workflow_status(wf, "supported", reason, [], None)
    return out


def _all_degraded(
    reason: str,
    missing: list[str],
    fallback: str,
) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for wf in REPORTING_WORKFLOWS:
        out[wf] = _workflow_status(wf, "degraded", reason, missing, fallback)
    return out


def _all_unavailable(reason: str, fallback: str | None) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for wf in REPORTING_WORKFLOWS:
        out[wf] = _workflow_status(
            wf, "unavailable", reason,
            ["LLM-based generation", "Workspace artifact writes"],
            fallback,
        )
    return out


# Workflow status per tier (status, reason, missing_functionality, fallback)
TIER_WORKFLOW_STATUS: dict[str, dict[str, dict[str, Any]]] = {
    "dev_full": _all_supported("Full stack: LLM backend, base_model, optional adapter and retrieval."),
    "local_standard": _all_supported(
        "Standard local: LLM required; adapter/retrieval optional (baseline fallback)."
    ),
    "constrained_edge": _all_degraded(
        "Constrained: LLM optional; with LLM runs baseline only. Without LLM workflows not runnable.",
        ["Adapter", "Retrieval", "Full sandbox"],
        "Provide LLM config for baseline runs; or use minimal_eval for eval-only.",
    ),
    "minimal_eval": _all_unavailable(
        "Eval-only tier: no reporting workspace or LLM.",
        "Use constrained_edge or local_standard for reporting; use this tier for eval harness only.",
    ),
}


def get_tier_definition(tier: str) -> dict[str, Any] | None:
    """Return tier definition (required_paths, llm_requirement, workflow_status) or None if unknown."""
    if tier not in EDGE_TIERS:
        return None
    return {
        "tier": tier,
        "required_paths": list(TIER_REQUIRED_PATHS.get(tier, ())),
        "llm_requirement": TIER_LLM_REQUIREMENT.get(tier, "required"),
        "workflow_status": dict(TIER_WORKFLOW_STATUS.get(tier, {})),
    }


def get_workflow_status_for_tier(tier: str) -> dict[str, dict[str, Any]]:
    """Return workflow -> { status, reason, missing_functionality, fallback } for tier."""
    if tier not in EDGE_TIERS:
        return {}
    return dict(TIER_WORKFLOW_STATUS.get(tier, {}))


def list_tiers() -> list[dict[str, Any]]:
    """List all tiers with summary (tier, required_paths_count, llm_requirement, supported_count, degraded_count, unavailable_count)."""
    out = []
    for t in EDGE_TIERS:
        defn = get_tier_definition(t)
        if not defn:
            continue
        status = defn.get("workflow_status") or {}
        supported = sum(1 for s in status.values() if (s or {}).get("status") == "supported")
        degraded = sum(1 for s in status.values() if (s or {}).get("status") == "degraded")
        unavailable = sum(1 for s in status.values() if (s or {}).get("status") == "unavailable")
        out.append({
            "tier": t,
            "required_paths_count": len(defn.get("required_paths") or []),
            "llm_requirement": defn.get("llm_requirement", "required"),
            "supported_count": supported,
            "degraded_count": degraded,
            "unavailable_count": unavailable,
        })
    return out

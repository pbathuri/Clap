"""
M23B: Edge profile — explicit runtime, storage, model, and sandbox assumptions. Local-only.
M23B-F2: Optional tier (dev_full, local_standard, constrained_edge, minimal_eval) scopes paths and workflow status.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# Reuse tier definitions when tier is set
try:
    from workflow_dataset.edge.tiers import (
        EDGE_TIERS,
        get_tier_definition,
        get_workflow_status_for_tier,
        TIER_DESCRIPTIONS,
        TIER_REQUIRED_PATHS,
    )
except ImportError:
    EDGE_TIERS = ()
    get_tier_definition = None
    get_workflow_status_for_tier = None
    TIER_DESCRIPTIONS = {}
    TIER_REQUIRED_PATHS = {}

# Sandbox paths the product expects under repo root (relative)
SANDBOX_PATHS = (
    "data/local/workspaces",
    "data/local/packages",
    "data/local/review",
    "data/local/pilot",
    "data/local/staging",
    "data/local/eval",
    "data/local/devlab",
    "data/local/incubator",
    "data/local/intake",
    "data/local/chains",
    "data/local/chains/runs",
    "data/local/templates",
    "data/local/llm",
    "configs",
)

# Workflows that are supported in edge/local deployment (ops/reporting family)
SUPPORTED_WORKFLOWS = (
    "weekly_status",
    "status_action_bundle",
    "stakeholder_update_bundle",
    "meeting_brief_bundle",
    "ops_reporting_workspace",
)


def _repo_root(root: Path | str | None) -> Path:
    if root is not None:
        return Path(root)
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root())
    except Exception:
        return Path.cwd()


def build_edge_profile(
    repo_root: Path | str | None = None,
    config_path: str = "configs/settings.yaml",
    tier: str | None = None,
) -> dict[str, Any]:
    """
    Build a reproducible local deployment profile: runtime requirements, storage assumptions,
    model/provider assumptions, sandbox paths. No cloud; no hardware device specs.
    If tier is set (dev_full, local_standard, constrained_edge, minimal_eval), profile is
    scoped to that tier: paths and workflow status follow tier definition.
    """
    root = _repo_root(repo_root)
    root = root.resolve()
    config_file = root / config_path
    tier_def = get_tier_definition(tier) if tier and get_tier_definition and tier in (EDGE_TIERS or ()) else None
    paths_for_profile = list(TIER_REQUIRED_PATHS.get(tier, SANDBOX_PATHS)) if tier_def else list(SANDBOX_PATHS)

    runtime: dict[str, Any] = {
        "python_version_min": "3.10",
        "python_version_recommended": "3.11",
        "python_version_current": f"{sys.version_info.major}.{sys.version_info.minor}",
        "no_cloud_required": True,
    }
    storage: dict[str, Any] = {
        "sandbox_under_repo": True,
        "paths": [{"path": p, "relative": p} for p in paths_for_profile],
        "writable_required": list(paths_for_profile),
    }
    model_assumptions: dict[str, Any] = {
        "local_llm_optional": True,
        "llm_config_path": "configs/llm_training_full.yaml",
        "adapter_runs_dir": "data/local/llm/runs",
        "corpus_path": "data/local/llm/corpus/corpus.jsonl",
    }
    sandbox_path_assumptions: dict[str, Any] = {
        "paths": list(paths_for_profile),
        "repo_root": str(root),
    }
    out: dict[str, Any] = {
        "repo_root": str(root),
        "config_path": str(config_file),
        "config_exists": config_file.exists(),
        "runtime_requirements": runtime,
        "storage_assumptions": storage,
        "model_assumptions": model_assumptions,
        "sandbox_path_assumptions": sandbox_path_assumptions,
        "supported_workflows": list(SUPPORTED_WORKFLOWS),
    }

    if tier_def and get_workflow_status_for_tier:
        status_map = get_workflow_status_for_tier(tier)
        supported_list = [wf for wf in SUPPORTED_WORKFLOWS if (status_map.get(wf) or {}).get("status") == "supported"]
        out["supported_workflows"] = supported_list
        out["tier"] = tier
        out["tier_description"] = TIER_DESCRIPTIONS.get(tier, "")
        out["tier_llm_requirement"] = tier_def.get("llm_requirement", "required")
        workflow_availability = []
        for wf in SUPPORTED_WORKFLOWS:
            ws = status_map.get(wf) or {}
            workflow_availability.append({
                "workflow": wf,
                "status": ws.get("status", "supported"),
                "reason": ws.get("reason", ""),
                "missing_functionality": ws.get("missing_functionality", []),
                "fallback": ws.get("fallback"),
            })
        out["workflow_availability"] = workflow_availability

    return out

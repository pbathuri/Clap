"""
M23B Module D: Edge packaging metadata.
Supported workflow matrix, required/optional dependencies, profile summary, missing dependency summary.
Local-only; for deployment testing and future appliance packaging.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.release.reporting_workspaces import REPORTING_WORKFLOWS
from workflow_dataset.release.workspace_export_contract import EXPORT_CONTRACTS

from workflow_dataset.edge.profile import build_edge_profile, SANDBOX_PATHS
from workflow_dataset.edge.checks import run_readiness_checks, checks_summary


def build_supported_workflow_matrix(
    repo_root: Path | str | None = None,
) -> list[dict[str, Any]]:
    """
    Build supported workflow matrix: workflow id, description, required files, optional files.
    """
    matrix: list[dict[str, Any]] = []
    for wf in REPORTING_WORKFLOWS:
        contract = EXPORT_CONTRACTS.get(wf)
        matrix.append({
            "workflow": wf,
            "description": (contract or {}).get("description", ""),
            "manifest_file": (contract or {}).get("manifest_file", "manifest.json"),
            "required_files": list((contract or {}).get("required_files") or []),
            "optional_files": list((contract or {}).get("optional_files") or []),
            "required_at_least_one_of": list((contract or {}).get("required_at_least_one_of") or []),
        })
    return matrix


def build_required_dependencies() -> list[dict[str, Any]]:
    """Required local dependencies for edge deployment."""
    return [
        {"name": "python", "type": "runtime", "note": "3.10+ recommended"},
        {"name": "typer", "type": "pip", "note": "CLI"},
        {"name": "rich", "type": "pip", "note": "console output"},
        {"name": "pyyaml", "type": "pip", "note": "configs"},
        {"name": "data/local", "type": "storage", "note": "sandbox root"},
        {"name": "LLM backend (mlx or openai)", "type": "runtime", "note": "required for full demo"},
        {"name": "base_model in LLM config", "type": "config", "note": "required for demo"},
    ]


def build_optional_dependencies() -> list[dict[str, Any]]:
    """Optional dependencies; product degrades gracefully when missing."""
    return [
        {"name": "mlx", "type": "pip", "note": "local LLM backend"},
        {"name": "transformers", "type": "pip", "note": "adapter training"},
        {"name": "adapter_path", "type": "artifact", "note": "fine-tuned adapter; baseline used if missing"},
        {"name": "corpus_path", "type": "config", "note": "retrieval corpus"},
        {"name": "configs/settings.yaml", "type": "config", "note": "setup/assist defaults if missing"},
        {"name": "configs/release_narrow.yaml", "type": "config", "note": "release defaults if missing"},
        {"name": "data/local/packs", "type": "storage", "note": "pack-driven trials"},
        {"name": "data/local/eval", "type": "storage", "note": "eval board"},
        {"name": "data/local/devlab", "type": "storage", "note": "devlab experiments"},
    ]


def _get_repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root())
    except Exception:
        return Path.cwd().resolve()


def build_missing_dependency_summary(
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Summarize missing dependencies from current environment and sandbox.
    Returns: missing_required, missing_optional, path_status, overall_ok.
    """
    root = _get_repo_root(repo_root)
    checks = run_readiness_checks(repo_root=root)
    summary = checks_summary(checks)
    failed_required = [c for c in checks if not c.get("passed") and not c.get("optional")]
    missing_required = [c.get("message", "") for c in failed_required]
    path_status: dict[str, bool] = {}
    for rel in SANDBOX_PATHS:
        path_status[rel] = (root / rel).exists()
    missing_optional = [rel for rel in SANDBOX_PATHS if not path_status.get(rel, False)]
    if not (root / "data" / "local").exists():
        try:
            (root / "data" / "local").mkdir(parents=True, exist_ok=True)
        except OSError:
            if "data/local" not in missing_required:
                missing_required.append("data/local")
    overall_ok = summary.get("ready", len(failed_required) == 0)
    return {
        "missing_required": missing_required,
        "missing_optional": missing_optional,
        "path_status": path_status,
        "overall_ok": overall_ok,
        "warnings": [c.get("message", "") for c in checks if not c.get("passed") and c.get("optional")],
    }


def build_edge_package_report(
    repo_root: Path | str | None = None,
    config_path: str | None = "configs/settings.yaml",
) -> dict[str, Any]:
    """
    Full edge package report: workflow matrix, required/optional deps, profile summary, missing deps.
    """
    profile = build_edge_profile(repo_root=repo_root, config_path=config_path)
    missing = build_missing_dependency_summary(repo_root=repo_root)
    runtime = profile.get("runtime_requirements") or {}
    return {
        "supported_workflow_matrix": build_supported_workflow_matrix(repo_root=repo_root),
        "required_dependencies": build_required_dependencies(),
        "optional_dependencies": build_optional_dependencies(),
        "profile_summary": {
            "repo_root": profile.get("repo_root"),
            "supported_workflows": profile.get("supported_workflows", []),
            "sandbox_paths_count": len(profile.get("sandbox_path_assumptions", {}).get("paths", [])),
            "runtime_python": runtime.get("python_version_min") or runtime.get("python_version_current"),
        },
        "missing_dependency_summary": missing,
        "profile_version": "1.0",
    }


# ----- M23B-F2: Workflow matrix by tier -----
def build_workflow_matrix_by_tier(
    tier: str,
    repo_root: Path | str | None = None,
) -> list[dict[str, Any]]:
    """
    Build workflow support matrix for a tier: each workflow has status (supported/degraded/unavailable),
    reason, missing_functionality, fallback. Uses EXPORT_CONTRACTS for description/required files.
    """
    from workflow_dataset.edge.tiers import (
        EDGE_TIERS,
        get_workflow_status_for_tier,
    )
    if tier not in EDGE_TIERS:
        return []
    status_map = get_workflow_status_for_tier(tier)
    matrix: list[dict[str, Any]] = []
    for wf in REPORTING_WORKFLOWS:
        contract = EXPORT_CONTRACTS.get(wf)
        ws = status_map.get(wf) or {}
        matrix.append({
            "workflow": wf,
            "description": (contract or {}).get("description", ""),
            "manifest_file": (contract or {}).get("manifest_file", "manifest.json"),
            "required_files": list((contract or {}).get("required_files") or []),
            "optional_files": list((contract or {}).get("optional_files") or []),
            "status": ws.get("status", "supported"),
            "reason": ws.get("reason", ""),
            "missing_functionality": list(ws.get("missing_functionality") or []),
            "fallback": ws.get("fallback"),
        })
    return matrix


def build_workflow_matrix_all_tiers(repo_root: Path | str | None = None) -> dict[str, list[dict[str, Any]]]:
    """Build workflow matrix for every tier. Keys: tier id, values: list of workflow rows."""
    from workflow_dataset.edge.tiers import EDGE_TIERS
    return {tier: build_workflow_matrix_by_tier(tier, repo_root=repo_root) for tier in EDGE_TIERS}


# ----- M23B-F3: Explicit edge packaging metadata (tier-scoped) -----
def build_packaging_metadata(
    tier: str,
    repo_root: Path | str | None = None,
    config_path: str = "configs/settings.yaml",
) -> dict[str, Any]:
    """
    Build explicit packaging metadata for a tier: required/optional runtime components,
    supported/degraded workflows, local path and config assumptions, notes for appliance packaging.
    For operator handoff to deployment or appliance efforts.
    """
    from workflow_dataset.edge.tiers import (
        EDGE_TIERS,
        TIER_DESCRIPTIONS,
        get_tier_definition,
        get_workflow_status_for_tier,
        get_required_dependencies_for_tier,
    )
    if tier not in EDGE_TIERS:
        return {"error": f"Unknown tier. Use one of: {list(EDGE_TIERS)}"}
    root = _get_repo_root(repo_root)
    profile = build_edge_profile(repo_root=root, config_path=config_path, tier=tier)
    missing = build_missing_dependency_summary(repo_root=root)
    defn = get_tier_definition(tier)
    status_map = get_workflow_status_for_tier(tier)
    required_deps, optional_deps = get_required_dependencies_for_tier(tier)

    supported = [wf for wf, s in status_map.items() if (s or {}).get("status") == "supported"]
    degraded = [wf for wf, s in status_map.items() if (s or {}).get("status") == "degraded"]
    unavailable = [wf for wf, s in status_map.items() if (s or {}).get("status") == "unavailable"]

    return {
        "tier": tier,
        "tier_description": TIER_DESCRIPTIONS.get(tier, ""),
        "required_runtime_components": [{"name": d["name"], "type": d["type"], "note": d.get("note", "")} for d in required_deps],
        "optional_runtime_components": [{"name": d["name"], "type": d["type"], "note": d.get("note", "")} for d in optional_deps],
        "supported_workflows": supported,
        "degraded_workflows": degraded,
        "unavailable_workflows": unavailable,
        "workflow_status": {wf: (s or {}).get("status") for wf, s in status_map.items()},
        "local_path_assumptions": list(defn.get("required_paths") or []),
        "config_assumptions": {
            "config_path": config_path,
            "config_exists": (root / config_path).exists(),
            "llm_requirement": defn.get("llm_requirement", "required"),
        },
        "missing_dependency_summary": {
            "overall_ok": missing.get("overall_ok"),
            "missing_required": missing.get("missing_required", []),
            "warnings": missing.get("warnings", []),
        },
        "notes_for_packaging": (
            "Local-only. No cloud. Use for deployment testing and appliance packaging. "
            "Run edge smoke-check --tier " + tier + " to validate runtime."
        ),
        "profile_version": "1.0",
    }

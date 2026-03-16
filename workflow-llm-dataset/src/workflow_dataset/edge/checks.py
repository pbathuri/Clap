"""
M23B: Readiness checks — can this setup run on a constrained local machine? Local-only.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from workflow_dataset.edge.profile import build_edge_profile, SANDBOX_PATHS


def run_readiness_checks(
    repo_root: Path | str | None = None,
    config_path: str = "configs/settings.yaml",
) -> list[dict[str, Any]]:
    """
    Run a set of readiness checks. Returns list of { check_id, passed, message, optional }.
    optional=True means the feature is disabled when check fails; optional=False means required.
    """
    root = Path(repo_root) if repo_root else Path.cwd()
    try:
        from workflow_dataset.path_utils import get_repo_root
        root = Path(get_repo_root()) if repo_root is None else root
    except Exception:
        pass
    root = root.resolve()
    results: list[dict[str, Any]] = []

    # Python version
    py_min = (3, 10)
    current = (sys.version_info.major, sys.version_info.minor)
    passed = current >= py_min
    results.append({
        "check_id": "python_version",
        "passed": passed,
        "message": f"Python {current[0]}.{current[1]} (min {py_min[0]}.{py_min[1]})",
        "optional": False,
    })

    # Config exists
    config_file = root / config_path
    results.append({
        "check_id": "config_exists",
        "passed": config_file.exists(),
        "message": str(config_file),
        "optional": False,
    })

    # Sandbox paths (existence; we do not create or write)
    core_required = ("data/local/workspaces", "data/local/review", "configs")
    for rel in SANDBOX_PATHS[:10]:
        p = root / rel
        if rel == "configs":
            passed = p.exists() and p.is_dir()
        else:
            passed = p.exists() and p.is_dir()
        results.append({
            "check_id": f"sandbox_{rel.replace('/', '_')}",
            "passed": passed,
            "message": f"{rel} {'exists' if passed else 'missing'}",
            "optional": rel not in core_required,
        })

    # LLM config optional
    llm_config = root / "configs/llm_training_full.yaml"
    results.append({
        "check_id": "llm_config",
        "passed": llm_config.exists(),
        "message": "LLM config present (required for release demo with adapter)",
        "optional": True,
    })

    return results


def checks_summary(checks: list[dict[str, Any]]) -> dict[str, Any]:
    """Return summary: passed, failed, failed_required, optional_disabled."""
    failed = [c for c in checks if not c.get("passed")]
    failed_required = [c for c in failed if not c.get("optional")]
    return {
        "passed": len([c for c in checks if c.get("passed")]),
        "failed": len(failed),
        "failed_required": len(failed_required),
        "optional_disabled": len([c for c in failed if c.get("optional")]),
        "ready": len(failed_required) == 0,
    }

"""
M51I–M51L: Degraded demo warnings from real state.
"""

from __future__ import annotations

from pathlib import Path

from workflow_dataset.investor_demo.models import DegradedDemoWarning


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def collect_degraded_warnings(repo_root: Path | str | None = None) -> list[DegradedDemoWarning]:
    out: list[DegradedDemoWarning] = []
    root = _root(repo_root)

    try:
        from workflow_dataset.validation.env_health import check_environment_health
        env = check_environment_health(root)
        if not env.get("required_ok", True):
            out.append(DegradedDemoWarning(
                warning_id="env_required_not_ok",
                message="Environment required checks did not pass. Acknowledge degraded demo mode.",
                source="env_health",
            ))
    except Exception as e:
        out.append(DegradedDemoWarning(
            warning_id="env_check_error",
            message=f"Could not verify environment: {e}",
            source="env_health",
        ))

    # Skip vertical/first-value scans when root is not the product repo (e.g. pytest tmp_path).
    if not (root / "pyproject.toml").exists():
        return out

    try:
        from workflow_dataset.vertical_excellence.compression import assess_first_value_stage
        stage = assess_first_value_stage(root)
        if stage.status == "blocked":
            out.append(DegradedDemoWarning(
                warning_id="first_value_blocked",
                message="First-value path reports blocked. Say so when presenting value.",
                source="vertical_excellence",
            ))
    except Exception:
        pass

    try:
        from workflow_dataset.vertical_excellence.path_resolver import get_chosen_vertical_id
        vid = get_chosen_vertical_id(root)
        if not vid or vid == "default":
            out.append(DegradedDemoWarning(
                warning_id="vertical_not_locked",
                message="No strong vertical lock; demo narrative is thinner.",
                source="vertical_selection",
            ))
    except Exception:
        pass

    return out

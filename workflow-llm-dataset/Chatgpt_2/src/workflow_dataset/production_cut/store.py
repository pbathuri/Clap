"""
M40A: Persist and load active production cut. data/local/production_cut/active_cut.json
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.production_cut.models import (
    ProductionCut,
    ChosenPrimaryVertical,
    SupportedWorkflowSet,
    RequiredTrustPosture,
    DefaultOperatingProfile,
    ProductionReadinessNote,
)


COHORT_DIR = "data/local/production_cut"
ACTIVE_CUT_FILE = "active_cut.json"


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _dir_path(repo_root: Path | str | None = None) -> Path:
    return _repo_root(repo_root) / COHORT_DIR


def _active_cut_path(repo_root: Path | str | None = None) -> Path:
    return _dir_path(repo_root) / ACTIVE_CUT_FILE


def _dict_to_cut(data: dict[str, Any]) -> ProductionCut:
    """Build ProductionCut from JSON dict."""
    cv = None
    if data.get("chosen_vertical"):
        cv_data = data["chosen_vertical"]
        cv = ChosenPrimaryVertical(
            vertical_id=cv_data.get("vertical_id", ""),
            label=cv_data.get("label", ""),
            description=cv_data.get("description", ""),
            selection_reason=cv_data.get("selection_reason", ""),
            primary_workflow_ids=cv_data.get("primary_workflow_ids", []),
            allowed_roles=cv_data.get("allowed_roles", []),
            allowed_modes=cv_data.get("allowed_modes", []),
            non_core_surface_ids=cv_data.get("non_core_surface_ids", []),
            excluded_surface_ids=cv_data.get("excluded_surface_ids", []),
        )
    sw = None
    if data.get("supported_workflows"):
        sw_data = data["supported_workflows"]
        sw = SupportedWorkflowSet(
            workflow_ids=sw_data.get("workflow_ids", []),
            path_id=sw_data.get("path_id", ""),
            label=sw_data.get("label", ""),
            description=sw_data.get("description", ""),
        )
    rt = None
    if data.get("required_trust"):
        rt_data = data["required_trust"]
        rt = RequiredTrustPosture(
            trust_preset_id=rt_data.get("trust_preset_id", ""),
            review_gates_default=rt_data.get("review_gates_default", []),
            audit_posture=rt_data.get("audit_posture", ""),
            description=rt_data.get("description", ""),
        )
    dp = None
    if data.get("default_profile"):
        dp_data = data["default_profile"]
        dp = DefaultOperatingProfile(
            workday_preset_id=dp_data.get("workday_preset_id", ""),
            default_experience_profile_id=dp_data.get("default_experience_profile_id", ""),
            queue_section_order=dp_data.get("queue_section_order", []),
            operator_mode_usage=dp_data.get("operator_mode_usage", ""),
            role_operating_hint=dp_data.get("role_operating_hint", ""),
        )
    prn = None
    if data.get("production_readiness_note"):
        prn_data = data["production_readiness_note"]
        prn = ProductionReadinessNote(
            summary=prn_data.get("summary", ""),
            blockers=prn_data.get("blockers", []),
            warnings=prn_data.get("warnings", []),
            last_updated_utc=prn_data.get("last_updated_utc", ""),
        )
    return ProductionCut(
        cut_id=data.get("cut_id", ""),
        vertical_id=data.get("vertical_id", ""),
        label=data.get("label", ""),
        frozen_at_utc=data.get("frozen_at_utc", ""),
        chosen_vertical=cv,
        included_surface_ids=data.get("included_surface_ids", []),
        excluded_surface_ids=data.get("excluded_surface_ids", []),
        quarantined_surface_ids=data.get("quarantined_surface_ids", []),
        supported_workflows=sw,
        required_trust=rt,
        default_profile=dp,
        production_readiness_note=prn,
    )


def get_active_cut(repo_root: Path | str | None = None) -> ProductionCut | None:
    """Load active production cut from disk; None if missing or invalid."""
    path = _active_cut_path(repo_root)
    if not path.exists() or not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return _dict_to_cut(data)
    except Exception:
        return None


def set_active_cut(cut: ProductionCut, repo_root: Path | str | None = None) -> Path:
    """Persist active production cut. Creates dir if needed."""
    path = _active_cut_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cut.to_dict(), indent=2), encoding="utf-8")
    return path

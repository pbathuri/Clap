"""
M47L.1: Recovery guidance packs for common vertical failures — what we know, recommend, need from user.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.quality_guidance.models import RecoveryGuidancePack


# Common failure patterns and vertical-agnostic pack
DEFAULT_RECOVERY_PACKS: list[RecoveryGuidancePack] = [
    RecoveryGuidancePack(
        pack_id="executor_blocked",
        vertical_id="",
        label="Executor run blocked",
        failure_patterns=["executor_blocked", "run_blocked"],
        what_we_know="A run is blocked at a checkpoint; recovery options are retry, skip, or substitute.",
        what_we_recommend="Resume from blocked: choose retry (same step again), skip (move to next step), or substitute (run a different bundle/action).",
        what_we_need_from_user="Your decision: retry | skip | substitute. For substitute, provide --substitute-bundle ID and optionally --note.",
        commands=[
            "workflow-dataset executor resume-from-blocked --run <run_id> --decision retry",
            "workflow-dataset executor resume-from-blocked --run <run_id> --decision skip",
            "workflow-dataset executor resume-from-blocked --run <run_id> --decision substitute --substitute-bundle <id>",
        ],
        escalation_ref="workflow-dataset executor hub get-recovery-options --run <run_id>",
    ),
    RecoveryGuidancePack(
        pack_id="vertical_onboarding_stalled",
        vertical_id="",
        label="Vertical onboarding stalled",
        failure_patterns=["onboarding_stalled", "first_value_blocked", "vertical_stalled"],
        what_we_know="First-value or onboarding path is blocked at a step; playbook has remediation for this step.",
        what_we_recommend="Follow the playbook remediation for the blocked step; run vertical-packs progress and use the suggested command.",
        what_we_need_from_user="Complete the suggested step (e.g. fix env, approve, or run simulate); then re-run first-value or progress.",
        commands=[
            "workflow-dataset vertical-packs progress",
            "workflow-dataset vertical-packs first-value --id <curated_pack_id>",
        ],
        escalation_ref="workflow-dataset vertical-packs playbook --id <pack_id>",
    ),
    RecoveryGuidancePack(
        pack_id="project_stalled",
        vertical_id="",
        label="Project / goal stalled",
        failure_patterns=["project_stalled", "stalled_projects", "replan_needed"],
        what_we_know="One or more projects are stalled or need replan; progress board has blockers and optional playbook match.",
        what_we_recommend="Run portfolio blocked and progress recovery for the project; apply playbook actions if matched.",
        what_we_need_from_user="Unblock the reported goal or approve replan; run progress recovery --project <id>.",
        commands=[
            "workflow-dataset portfolio blocked",
            "workflow-dataset progress recovery --project <project_id>",
            "workflow-dataset portfolio explain --project <project_id>",
        ],
        escalation_ref="workflow-dataset progress board",
    ),
    RecoveryGuidancePack(
        pack_id="founder_operator_blocked",
        vertical_id="founder_operator_core",
        label="Founder operator vertical blocked",
        failure_patterns=["founder_operator_blocked", "first_value_blocked"],
        what_we_know="Founder-operator first-value path or onboarding is blocked; operator playbook has step-level recovery.",
        what_we_recommend="Use vertical-packs first-value and progress for founder_operator_core; follow remediation hint for the blocked step.",
        what_we_need_from_user="Complete the step (setup, approval, or run); then re-run progress or first-value.",
        commands=[
            "workflow-dataset vertical-packs progress",
            "workflow-dataset vertical-packs first-value --id founder_operator_core",
        ],
        escalation_ref="workflow-dataset vertical-packs playbook --id founder_operator_core",
    ),
]


def get_default_recovery_packs() -> list[RecoveryGuidancePack]:
    return list(DEFAULT_RECOVERY_PACKS)


def get_recovery_pack_for_failure_pattern(
    pattern: str,
    repo_root: Path | str | None = None,
) -> RecoveryGuidancePack | None:
    """Return first pack whose failure_patterns contain pattern."""
    pattern_lower = (pattern or "").lower()
    for pack in DEFAULT_RECOVERY_PACKS:
        if any(pattern_lower in (p or "").lower() for p in pack.failure_patterns):
            return pack
    return None


def get_recovery_pack_for_vertical(
    vertical_id: str,
    repo_root: Path | str | None = None,
) -> RecoveryGuidancePack | None:
    """Return pack whose vertical_id matches, or first pack with empty vertical_id as fallback."""
    vid = (vertical_id or "").strip()
    for pack in DEFAULT_RECOVERY_PACKS:
        if pack.vertical_id == vid:
            return pack
    for pack in DEFAULT_RECOVERY_PACKS:
        if not pack.vertical_id:
            return pack
    return None


def load_custom_recovery_packs(repo_root: Path | str | None = None) -> list[RecoveryGuidancePack]:
    """Load custom packs from data/local/quality_guidance/recovery_packs.json if present."""
    root = _repo_root(repo_root)
    path = root / "data/local/quality_guidance/recovery_packs.json"
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        packs = data if isinstance(data, list) else data.get("packs", [])
        return [_pack_from_dict(p) for p in packs if isinstance(p, dict)]
    except Exception:
        return []


def _pack_from_dict(d: dict[str, Any]) -> RecoveryGuidancePack:
    return RecoveryGuidancePack(
        pack_id=d.get("pack_id", ""),
        vertical_id=d.get("vertical_id", ""),
        label=d.get("label", ""),
        failure_patterns=list(d.get("failure_patterns", [])),
        what_we_know=d.get("what_we_know", ""),
        what_we_recommend=d.get("what_we_recommend", ""),
        what_we_need_from_user=d.get("what_we_need_from_user", ""),
        commands=list(d.get("commands", [])),
        escalation_ref=d.get("escalation_ref", ""),
    )


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()

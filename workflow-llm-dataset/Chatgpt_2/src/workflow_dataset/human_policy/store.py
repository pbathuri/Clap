"""
M28I–M28L: Human policy store — load/save policy config and overrides.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.human_policy.models import (
    HumanPolicyConfig,
    OverrideRecord,
    ActionClassPolicy,
    ApprovalRequirementPolicy,
    DelegationPolicy,
    ExceptionPolicy,
    ACTION_EXECUTE_SIMULATE,
    ACTION_PLANNER_COMPILE,
    ACTION_EXECUTE_TRUSTED_REAL,
    ACTION_EXECUTOR_RESUME,
    ACTION_DELEGATE_GOAL,
    ACTION_USE_WORKER_LANE,
    ACTION_ROUTING,
)

POLICY_DIR = "data/local/human_policy"
CONFIG_FILE = "policy_config.json"
OVERRIDES_FILE = "overrides.json"


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def get_policy_dir(repo_root: Path | str | None = None) -> Path:
    return _repo_root(repo_root) / POLICY_DIR


def _default_config() -> HumanPolicyConfig:
    """Safe defaults: everything requires approval, no delegation, no batch by default."""
    return HumanPolicyConfig(
        action_class_policies=[
            ActionClassPolicy(action_class=ACTION_EXECUTE_SIMULATE, allow_auto=False, require_approval=True, allow_batch=True),
            ActionClassPolicy(action_class=ACTION_PLANNER_COMPILE, allow_auto=False, require_approval=True, allow_batch=True),
            ActionClassPolicy(action_class=ACTION_EXECUTE_TRUSTED_REAL, allow_auto=False, require_approval=True, allow_batch=False),
            ActionClassPolicy(action_class=ACTION_EXECUTOR_RESUME, allow_auto=False, require_approval=True, allow_batch=False),
            ActionClassPolicy(action_class=ACTION_DELEGATE_GOAL, allow_auto=False, require_approval=True, allow_batch=False),
            ActionClassPolicy(action_class=ACTION_USE_WORKER_LANE, allow_auto=False, require_approval=True, allow_batch=False),
            ActionClassPolicy(action_class=ACTION_ROUTING, allow_auto=True, require_approval=False, allow_batch=False),
        ],
        approval_defaults=ApprovalRequirementPolicy(always_manual=True, may_batch_for_risk="low"),
        delegation_default=DelegationPolicy(may_delegate=False),
        exception_policy=ExceptionPolicy(allow_exceptions=False, expiry_hours=24),
    )


def load_policy_config(repo_root: Path | str | None = None) -> HumanPolicyConfig:
    path = get_policy_dir(repo_root) / CONFIG_FILE
    if not path.exists():
        return _default_config()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return HumanPolicyConfig.from_dict(data)
    except Exception:
        return _default_config()


def save_policy_config(config: HumanPolicyConfig, repo_root: Path | str | None = None) -> Path:
    get_policy_dir(repo_root).mkdir(parents=True, exist_ok=True)
    path = get_policy_dir(repo_root) / CONFIG_FILE
    path.write_text(json.dumps(config.to_dict(), indent=2), encoding="utf-8")
    return path


def load_overrides(repo_root: Path | str | None = None) -> list[OverrideRecord]:
    path = get_policy_dir(repo_root) / OVERRIDES_FILE
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return [OverrideRecord.from_dict(x) for x in data.get("overrides", [])]
    except Exception:
        return []


def save_overrides(records: list[OverrideRecord], repo_root: Path | str | None = None) -> Path:
    get_policy_dir(repo_root).mkdir(parents=True, exist_ok=True)
    path = get_policy_dir(repo_root) / OVERRIDES_FILE
    path.write_text(json.dumps({"overrides": [r.to_dict() for r in records]}, indent=2), encoding="utf-8")
    return path

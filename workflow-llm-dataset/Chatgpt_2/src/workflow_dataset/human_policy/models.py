"""
M28I–M28L: Human policy engine — explicit models for operator governance.
Local, inspectable; no hidden policy.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Scopes: precedence project > pack > task > lane > global (more specific overrides less)
SCOPE_GLOBAL = "global"
SCOPE_PROJECT = "project"
SCOPE_PACK = "pack"
SCOPE_TASK = "task"
SCOPE_LANE = "lane"
POLICY_SCOPES = (SCOPE_GLOBAL, SCOPE_PROJECT, SCOPE_PACK, SCOPE_TASK, SCOPE_LANE)

# Action classes the engine can govern
ACTION_EXECUTE_SIMULATE = "execute_simulate"
ACTION_EXECUTE_TRUSTED_REAL = "execute_trusted_real"
ACTION_PLANNER_COMPILE = "planner_compile"
ACTION_EXECUTOR_RESUME = "executor_resume"
ACTION_DELEGATE_GOAL = "delegate_goal"
ACTION_USE_WORKER_LANE = "use_worker_lane"
ACTION_ROUTING = "routing"
ACTION_CLASSES = (
    ACTION_EXECUTE_SIMULATE,
    ACTION_EXECUTE_TRUSTED_REAL,
    ACTION_PLANNER_COMPILE,
    ACTION_EXECUTOR_RESUME,
    ACTION_DELEGATE_GOAL,
    ACTION_USE_WORKER_LANE,
    ACTION_ROUTING,
)


@dataclass
class ActionClassPolicy:
    """Per action-class: allow auto, require approval, allow batch."""
    action_class: str = ""
    allow_auto: bool = False
    require_approval: bool = True
    allow_batch: bool = False


@dataclass
class ApprovalRequirementPolicy:
    """Scope-level: default approval requirement (always_manual, may_batch)."""
    scope: str = SCOPE_GLOBAL
    scope_id: str = ""
    always_manual: bool = True
    may_batch_for_risk: str = ""  # "" | "low" | "medium"


@dataclass
class DelegationPolicy:
    """Whether goals/work may be delegated at this scope."""
    scope: str = SCOPE_GLOBAL
    scope_id: str = ""
    may_delegate: bool = False


@dataclass
class RoutingPriorityOverride:
    """Override routing/planning priority (e.g. prefer_lane, prefer_pack)."""
    scope: str = SCOPE_GLOBAL
    scope_id: str = ""
    priority_key: str = ""
    priority_value: str = ""


@dataclass
class BlockedActionPolicy:
    """Explicit list of blocked action classes at scope."""
    scope: str = SCOPE_GLOBAL
    scope_id: str = ""
    blocked_action_classes: list[str] = field(default_factory=list)


@dataclass
class ExceptionPolicy:
    """Whether exceptions may be granted, by whom, expiry."""
    allow_exceptions: bool = False
    granted_by_scope: str = SCOPE_GLOBAL
    expiry_hours: int = 24


@dataclass
class HumanPolicyConfig:
    """Root policy config: defaults and scope-specific rules. Loaded from JSON."""
    # Global action-class defaults
    action_class_policies: list[ActionClassPolicy] = field(default_factory=list)
    approval_defaults: ApprovalRequirementPolicy = field(default_factory=lambda: ApprovalRequirementPolicy(always_manual=True))
    delegation_default: DelegationPolicy = field(default_factory=lambda: DelegationPolicy(may_delegate=False))
    routing_overrides: list[RoutingPriorityOverride] = field(default_factory=list)
    blocked_actions: list[BlockedActionPolicy] = field(default_factory=list)
    exception_policy: ExceptionPolicy = field(default_factory=ExceptionPolicy)
    # Project-level simulate_only (project_id -> True means that project must stay simulate)
    project_simulate_only: dict[str, bool] = field(default_factory=dict)
    # Pack may override defaults (pack_id -> True)
    pack_may_override_defaults: dict[str, bool] = field(default_factory=dict)
    # M28L.1: Active preset name when config was applied from a preset ("" = custom)
    active_preset: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_class_policies": [
                {"action_class": p.action_class, "allow_auto": p.allow_auto, "require_approval": p.require_approval, "allow_batch": p.allow_batch}
                for p in self.action_class_policies
            ],
            "approval_defaults": {
                "scope": self.approval_defaults.scope,
                "always_manual": self.approval_defaults.always_manual,
                "may_batch_for_risk": self.approval_defaults.may_batch_for_risk,
            },
            "delegation_default": {"scope": self.delegation_default.scope, "may_delegate": self.delegation_default.may_delegate},
            "routing_overrides": [
                {"scope": r.scope, "scope_id": r.scope_id, "priority_key": r.priority_key, "priority_value": r.priority_value}
                for r in self.routing_overrides
            ],
            "blocked_actions": [
                {"scope": b.scope, "scope_id": b.scope_id, "blocked_action_classes": list(b.blocked_action_classes)}
                for b in self.blocked_actions
            ],
            "exception_policy": {
                "allow_exceptions": self.exception_policy.allow_exceptions,
                "granted_by_scope": self.exception_policy.granted_by_scope,
                "expiry_hours": self.exception_policy.expiry_hours,
            },
            "project_simulate_only": dict(self.project_simulate_only),
            "pack_may_override_defaults": dict(self.pack_may_override_defaults),
            "active_preset": self.active_preset,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any] | None) -> "HumanPolicyConfig":
        if not d:
            return cls()
        acp = [ActionClassPolicy(
            action_class=x.get("action_class", ""),
            allow_auto=bool(x.get("allow_auto", False)),
            require_approval=bool(x.get("require_approval", True)),
            allow_batch=bool(x.get("allow_batch", False)),
        ) for x in d.get("action_class_policies", [])]
        app = d.get("approval_defaults") or {}
        approval = ApprovalRequirementPolicy(
            scope=app.get("scope", SCOPE_GLOBAL),
            always_manual=bool(app.get("always_manual", True)),
            may_batch_for_risk=str(app.get("may_batch_for_risk", "")),
        )
        del_default = d.get("delegation_default") or {}
        delegation = DelegationPolicy(
            scope=del_default.get("scope", SCOPE_GLOBAL),
            may_delegate=bool(del_default.get("may_delegate", False)),
        )
        routing = [RoutingPriorityOverride(
            scope=r.get("scope", ""),
            scope_id=r.get("scope_id", ""),
            priority_key=r.get("priority_key", ""),
            priority_value=r.get("priority_value", ""),
        ) for r in d.get("routing_overrides", [])]
        blocked = [BlockedActionPolicy(
            scope=b.get("scope", ""),
            scope_id=b.get("scope_id", ""),
            blocked_action_classes=list(b.get("blocked_action_classes", [])),
        ) for b in d.get("blocked_actions", [])]
        ex = d.get("exception_policy") or {}
        exception = ExceptionPolicy(
            allow_exceptions=bool(ex.get("allow_exceptions", False)),
            granted_by_scope=str(ex.get("granted_by_scope", SCOPE_GLOBAL)),
            expiry_hours=int(ex.get("expiry_hours", 24)),
        )
        return cls(
            action_class_policies=acp,
            approval_defaults=approval,
            delegation_default=delegation,
            routing_overrides=routing,
            blocked_actions=blocked,
            exception_policy=exception,
            project_simulate_only=dict(d.get("project_simulate_only") or {}),
            pack_may_override_defaults=dict(d.get("pack_may_override_defaults") or {}),
            active_preset=str(d.get("active_preset", "")),
        )


@dataclass
class OverrideRecord:
    """Temporary override: scope + id + rule key/value, optional expiry."""
    override_id: str = ""
    scope: str = ""
    scope_id: str = ""
    rule_key: str = ""
    rule_value: Any = None
    reason: str = ""
    created_at: str = ""
    expires_at: str = ""
    revoked_at: str = ""

    def is_active(self, now_iso: str = "") -> bool:
        if self.revoked_at:
            return False
        if self.expires_at and now_iso and self.expires_at < now_iso:
            return False
        return True

    def to_dict(self) -> dict[str, Any]:
        return {
            "override_id": self.override_id,
            "scope": self.scope,
            "scope_id": self.scope_id,
            "rule_key": self.rule_key,
            "rule_value": self.rule_value,
            "reason": self.reason,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "revoked_at": self.revoked_at,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "OverrideRecord":
        return cls(
            override_id=d.get("override_id", ""),
            scope=d.get("scope", ""),
            scope_id=d.get("scope_id", ""),
            rule_key=d.get("rule_key", ""),
            rule_value=d.get("rule_value"),
            reason=d.get("reason", ""),
            created_at=d.get("created_at", ""),
            expires_at=d.get("expires_at", ""),
            revoked_at=d.get("revoked_at", ""),
        )

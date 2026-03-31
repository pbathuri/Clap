"""
Core models for the macOS local operator draft.
Shared core state; shaped summaries should be derived elsewhere.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


SCOPE_ORIGINS = (
    "approved_folder",
    "approved_app",
    "session_trust",
    "policy_default",
    "explicit_one_time_approval",
)

ADAPTER_MODES = (
    "none",
    "simulated",
    "propose_only",
    "supervised_live",
    "session_trusted_live",
)


@dataclass
class ApprovedFolderEntry:
    path: str
    allowed_operations: list[str] = field(default_factory=list)
    recursive: bool = True
    inherit_mode: str = "inherit"
    sensitivity_tag: str = "unspecified"
    approval_source: str = "explicit_user"
    revocation_state: str = "active"
    approved_at: str = ""
    reviewed_at: str = ""
    expires_at: str = ""


@dataclass
class WorkflowTreeNode:
    node_id: str
    node_type: str
    parent_id: str = ""
    title: str = ""
    children: list[str] = field(default_factory=list)
    inferred_tools: list[str] = field(default_factory=list)
    inferred_data_dependencies: list[str] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    evidence_summary: str = ""
    confidence: float | None = None
    confidence_reason: str = ""
    missing_evidence: list[str] = field(default_factory=list)
    suggested_next_actions: list[str] = field(default_factory=list)
    execution_eligibility: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolEntry:
    tool_id: str
    label: str = ""
    installed: bool = False
    inferred: bool = False
    actively_relevant: bool = False
    adapter_supported: bool = False
    permission_ready: bool = False
    adapter_mode: str = "none"
    evidence_refs: list[str] = field(default_factory=list)


@dataclass
class ActionProposal:
    action_id: str
    title: str = ""
    label: str = ""
    risk_tier: str = ""
    destructive: bool = False
    reversible: bool = True
    approval_requirement: str = "explicit"
    execution_scope: dict[str, Any] = field(default_factory=dict)
    required_adapter: str = ""
    required_permissions: list[str] = field(default_factory=list)
    scope_origin: str = ""
    rationale: str = ""
    evidence_refs: list[str] = field(default_factory=list)
    rollback_feasible: bool = True
    rollback_method: str = "none"


@dataclass
class SessionTrustState:
    trust_state: str = ""
    trusted_until: str = ""
    notes: list[str] = field(default_factory=list)


@dataclass
class CapabilityTrustState:
    capability_id: str
    ready: bool = False
    notes: list[str] = field(default_factory=list)


@dataclass
class LocalOperatorState:
    approved_folders: list[ApprovedFolderEntry] = field(default_factory=list)
    workflow_tree: list[WorkflowTreeNode] = field(default_factory=list)
    tool_registry: list[ToolEntry] = field(default_factory=list)
    action_proposals: list[ActionProposal] = field(default_factory=list)
    session_trust: SessionTrustState = field(default_factory=SessionTrustState)
    capability_trust: list[CapabilityTrustState] = field(default_factory=list)
    machine_readiness: dict[str, Any] = field(default_factory=dict)
    operator_readiness: dict[str, Any] = field(default_factory=dict)
    updated_at: str = ""

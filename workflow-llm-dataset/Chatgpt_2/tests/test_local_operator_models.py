"""Schema / serialization expectations for local_operator core models."""

from __future__ import annotations

from dataclasses import asdict

from workflow_dataset.local_operator.models import (
    ActionProposal,
    ApprovedFolderEntry,
    CapabilityTrustState,
    LocalOperatorState,
    SessionTrustState,
    ToolEntry,
    WorkflowTreeNode,
)


def test_approved_folder_entry_asdict_keys() -> None:
    e = ApprovedFolderEntry(path="/tmp/proj", allowed_operations=["read", "open"])
    d = asdict(e)
    assert d["path"] == "/tmp/proj"
    assert "read" in d["allowed_operations"]
    assert d["revocation_state"] == "active"


def test_workflow_tree_node_asdict_shape() -> None:
    n = WorkflowTreeNode(
        node_id="n1",
        node_type="root",
        title="Root",
        evidence_refs=["file:README.md"],
    )
    d = asdict(n)
    assert d["node_id"] == "n1"
    assert d["node_type"] == "root"
    assert "children" in d and isinstance(d["children"], list)


def test_tool_entry_classification_fields() -> None:
    t = ToolEntry(
        tool_id="vscode",
        installed=True,
        inferred=True,
        actively_relevant=False,
        adapter_supported=True,
        permission_ready=True,
        adapter_mode="supervised_live",
    )
    d = asdict(t)
    assert d["installed"] is True
    assert d["adapter_mode"] == "supervised_live"


def test_action_proposal_risk_and_rollback_fields() -> None:
    p = ActionProposal(
        action_id="a1",
        risk_tier="low",
        destructive=False,
        reversible=True,
        scope_origin="approved_folder",
        rollback_feasible=True,
        rollback_method="none",
    )
    d = asdict(p)
    assert d["risk_tier"] == "low"
    assert d["rollback_feasible"] is True


def test_session_vs_capability_trust_distinct() -> None:
    s = SessionTrustState(trust_state="none", trusted_until="")
    c = CapabilityTrustState(capability_id="finder_open", ready=False)
    st = LocalOperatorState(session_trust=s, capability_trust=[c])
    out = asdict(st)
    assert isinstance(out["session_trust"], dict)
    assert len(out["capability_trust"]) == 1

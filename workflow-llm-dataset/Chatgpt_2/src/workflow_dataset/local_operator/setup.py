"""
Setup/status helpers for local operator.
"""

from __future__ import annotations

from typing import Any
from pathlib import Path

from workflow_dataset.local_operator.state_store import load_operator_state, save_operator_state
from workflow_dataset.local_operator.readiness import build_machine_readiness, build_operator_readiness
from workflow_dataset.local_operator.permissions import check_capabilities


def build_setup_status(repo_root: Path | str | None = None) -> dict[str, Any]:
    state = load_operator_state(repo_root)
    capability_trust = check_capabilities()
    machine = build_machine_readiness(repo_root)
    operator = build_operator_readiness(repo_root)
    state["capability_trust"] = capability_trust
    state["machine_readiness"] = machine
    state["operator_readiness"] = operator
    save_operator_state(state, repo_root)
    return {
        "machine_readiness": machine,
        "operator_readiness": operator,
        "session_trust": state.get("session_trust") or {},
        "capability_trust": capability_trust,
    }

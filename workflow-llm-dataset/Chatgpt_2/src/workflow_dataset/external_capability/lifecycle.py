"""
M24G: Capability lifecycle — installed / configured / active / blocked / failed.
Derive from backend status, integration enabled, activation history.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.external_capability.schema import LIFECYCLE_STATES
from workflow_dataset.external_capability.registry import get_external_source
from workflow_dataset.external_capability.activation_store import load_history


def source_lifecycle_state(
    source_id: str,
    repo_root: Path | str | None = None,
) -> str:
    """
    Return lifecycle state for a source: installed | configured | active | blocked | failed | unknown.
    - active: enabled and (available or configured)
    - configured: not enabled but backend/manifest present
    - installed: present but not configured for use
    - blocked: policy or approval blocked
    - failed: last activation attempt failed
    - unknown: not in registry or cannot determine
    """
    root = Path(repo_root).resolve() if repo_root else Path.cwd()
    source = get_external_source(source_id, root)
    if not source:
        return "unknown"

    # Check for failed activation request for this source
    from workflow_dataset.external_capability.activation_store import list_requests
    failed_reqs = list_requests(root, status="failed")
    for r in failed_reqs:
        if r.source_id == source_id:
            return "failed"

    if source.enabled:
        if source.activation_status in ("available", "configured"):
            return "active"
        return "configured"
    if source.activation_status in ("available", "configured"):
        return "configured"
    if source.activation_status == "blocked":
        return "blocked"
    if source.activation_status in ("missing", "not_installed"):
        return "installed"  # present in registry but not installed locally
    return "unknown"

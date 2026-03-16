"""
M21Z: Proposal queue: list, show, update status and operator notes. No auto-apply.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.devlab.config import get_proposals_dir, get_devlab_root


def list_proposals(root: Path | str | None = None) -> list[dict[str, Any]]:
    """List all proposals (from manifest.json in each proposal dir). Newest first."""
    prop_dir = get_proposals_dir(root)
    if not prop_dir.exists():
        return []
    out: list[dict[str, Any]] = []
    for d in prop_dir.iterdir():
        if not d.is_dir():
            continue
        m = d / "manifest.json"
        if not m.exists():
            continue
        try:
            data = json.loads(m.read_text(encoding="utf-8"))
            data["proposal_path"] = str(d)
            out.append(data)
        except Exception:
            pass
    for o in out:
        if "proposal_id" not in o and o.get("created_at"):
            o["proposal_id"] = Path(o.get("proposal_path", "")).name or ""
    out.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return out


def resolve_proposal_id(proposal_id: str, root: Path | str | None = None) -> str | None:
    """Resolve proposal_id: 'latest' -> newest proposal id; otherwise return id if it exists."""
    if (proposal_id or "").strip().lower() == "latest":
        proposals = list_proposals(root)
        if not proposals:
            return None
        return proposals[0].get("proposal_id") or Path(proposals[0].get("proposal_path", "")).name or None
    prop_dir = get_proposals_dir(root) / proposal_id
    if prop_dir.exists() and prop_dir.is_dir() and (prop_dir / "manifest.json").exists():
        return proposal_id
    return None


def get_proposal(proposal_id: str, root: Path | str | None = None) -> dict[str, Any] | None:
    """Load proposal manifest and paths to artifacts. proposal_id may be 'latest'."""
    resolved = resolve_proposal_id(proposal_id, root)
    if not resolved:
        return None
    prop_dir = get_proposals_dir(root) / resolved
    if not prop_dir.exists() or not prop_dir.is_dir():
        return None
    m = prop_dir / "manifest.json"
    if not m.exists():
        return None
    try:
        data = json.loads(m.read_text(encoding="utf-8"))
        data["proposal_path"] = str(prop_dir)
        for name in (
            "experiment_report.md",
            "patch_proposal.md",
            "devlab_proposal.md",
            "cursor_prompt.txt",
            "rfc_skeleton.md",
        ):
            if (prop_dir / name).exists():
                data[name.replace(".", "_")] = str(prop_dir / name)
        return data
    except Exception:
        return None


def update_proposal_status(proposal_id: str, status: str, operator_notes: str = "", root: Path | str | None = None) -> bool:
    """Update proposal status: pending | reviewed | accepted | rejected. Optionally set operator_notes."""
    prop_dir = get_proposals_dir(root) / proposal_id
    m = prop_dir / "manifest.json"
    if not m.exists():
        return False
    try:
        data = json.loads(m.read_text(encoding="utf-8"))
        data["status"] = status
        if operator_notes is not None:
            data["operator_notes"] = operator_notes
        m.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return True
    except Exception:
        return False


def proposal_queue_summary(root: Path | str | None = None) -> dict[str, Any]:
    """Count by status: pending, reviewed, accepted, rejected."""
    proposals = list_proposals(root)
    counts = {"pending": 0, "reviewed": 0, "accepted": 0, "rejected": 0}
    for p in proposals:
        s = p.get("status", "pending")
        if s in counts:
            counts[s] += 1
    return {"total": len(proposals), **counts}

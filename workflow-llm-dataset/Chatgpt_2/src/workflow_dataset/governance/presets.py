"""
M48D.1: Governance presets — solo operator, supervised team, production maintainer.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.governance.models import GovernancePreset

GOVERNANCE_DIR = "data/local/governance"
ACTIVE_PRESET_FILE = "active_preset.json"


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _builtin_presets() -> list[GovernancePreset]:
    return [
        GovernancePreset(
            preset_id="solo_operator",
            label="Solo operator",
            description="Single operator; no separation of duties. Best for local or dev use.",
            primary_role_id="operator",
            trust_preset_id="supervised_operator",
            scope_template_id="solo_vertical",
            implications=[
                "You are the only role; operator with queue/simulate and approval-gated real run.",
                "No reviewer/approver separation; use trust cockpit to grant yourself approvals when appropriate.",
                "Audit and reversibility still apply; keep trust preset in mind.",
            ],
            allowed_role_ids=["operator", "observer"],
            order=0,
        ),
        GovernancePreset(
            preset_id="supervised_team",
            label="Supervised team",
            description="Operator + reviewer/approver; separation of duties for real run and sensitive gates.",
            primary_role_id="operator",
            trust_preset_id="supervised_operator",
            scope_template_id="team_vertical_project",
            implications=[
                "Operator executes; reviewer/approver signs off on real run and sensitive gates.",
                "Initiator cannot self-approve in sensitive domains; use review studio for approvals.",
                "Escalate to support_reviewer or maintainer when blocked.",
            ],
            allowed_role_ids=["operator", "reviewer", "approver", "observer", "support_reviewer"],
            order=1,
        ),
        GovernancePreset(
            preset_id="production_maintainer",
            label="Production maintainer",
            description="Maintainer-led; full scope within vertical with audit and bounded trusted real.",
            primary_role_id="maintainer",
            trust_preset_id="release_safe",
            scope_template_id="production_single_vertical",
            implications=[
                "Maintainer may operate, review, and approve within the vertical; bounded_trusted_real with audit.",
                "No commit_or_send in production path without explicit approval and audit.",
                "Use stability reviews and deployment decision packs for go/no-go.",
            ],
            allowed_role_ids=["maintainer", "operator", "reviewer", "approver", "observer", "support_reviewer"],
            order=2,
        ),
    ]


def list_presets() -> list[GovernancePreset]:
    """Return all built-in governance presets in order."""
    return list(_builtin_presets())


def get_preset(preset_id: str) -> GovernancePreset | None:
    """Return built-in preset by id."""
    for p in _builtin_presets():
        if p.preset_id == preset_id:
            return p
    return None


def get_governance_dir(repo_root: Path | str | None = None) -> Path:
    """Return data/local/governance directory."""
    return _root(repo_root) / GOVERNANCE_DIR


def get_active_preset(repo_root: Path | str | None = None) -> GovernancePreset | None:
    """Return active preset from data/local/governance/active_preset.json; else default solo_operator."""
    root = _root(repo_root)
    path = get_governance_dir(root) / ACTIVE_PRESET_FILE
    if not path.exists():
        return get_preset("solo_operator")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        pid = data.get("preset_id", "")
        return get_preset(pid) if pid else get_preset("solo_operator")
    except Exception:
        return get_preset("solo_operator")


def set_active_preset(preset_id: str, repo_root: Path | str | None = None) -> Path:
    """Persist active preset id; returns path written."""
    if get_preset(preset_id) is None:
        raise ValueError(f"Unknown governance preset: {preset_id}")
    root = get_governance_dir(repo_root)
    root.mkdir(parents=True, exist_ok=True)
    path = root / ACTIVE_PRESET_FILE
    from datetime import datetime, timezone
    data = {
        "preset_id": preset_id,
        "applied_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path

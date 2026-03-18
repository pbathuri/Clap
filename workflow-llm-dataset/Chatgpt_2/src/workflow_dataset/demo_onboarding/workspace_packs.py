"""
M51H.1: Sample workspace packs — bounded folders for consistent investor-demo bootstrap.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.demo_onboarding.models import SampleWorkspacePack

SAMPLE_WORKSPACE_PACKS: dict[str, SampleWorkspacePack] = {
    "acme_operator_default": SampleWorkspacePack(
        pack_id="acme_operator_default",
        label="Acme operator (primary investor demo)",
        description="Weekly status, priorities, follow-ups — matches founder/operator narrative.",
        path_relative="docs/samples/demo_onboarding_workspace",
        suggested_role_preset_ids=["founder_operator_demo"],
        demo_talking_points=[
            "Small bounded sample — not the user's whole machine.",
            "Memory bootstrap picks up project folder name and priority lines from markdown.",
        ],
    ),
    "document_review_slice": SampleWorkspacePack(
        pack_id="document_review_slice",
        label="Document review slice",
        description="Draft + review queue snippets for document-heavy demo path.",
        path_relative="docs/samples/demo_workspace_document_review",
        suggested_role_preset_ids=["document_review_demo"],
        demo_talking_points=[
            "Shows how review-oriented filenames and todos surface in bootstrap.",
        ],
    ),
    "analyst_followup_slice": SampleWorkspacePack(
        pack_id="analyst_followup_slice",
        label="Analyst follow-up slice",
        description="Sprint-style notes and stakeholder follow-ups for analyst preset.",
        path_relative="docs/samples/demo_workspace_analyst",
        suggested_role_preset_ids=["analyst_followup_demo"],
        demo_talking_points=[
            "Recurring themes from short notes — still heuristic, bounded sample.",
        ],
    ),
}


def get_workspace_pack(pack_id: str) -> SampleWorkspacePack | None:
    return SAMPLE_WORKSPACE_PACKS.get(pack_id)


def list_workspace_pack_ids() -> list[str]:
    return list(SAMPLE_WORKSPACE_PACKS.keys())


def resolve_workspace_pack_path(pack_id: str, repo_root: Path | str | None = None) -> Path | None:
    """Absolute path to pack folder if it exists."""
    p = get_workspace_pack(pack_id)
    if not p or not p.path_relative:
        return None
    if repo_root is not None:
        root = Path(repo_root).resolve()
    else:
        try:
            from workflow_dataset.path_utils import get_repo_root
            root = Path(get_repo_root()).resolve()
        except Exception:
            root = Path.cwd().resolve()
    path = (root / p.path_relative).resolve()
    return path if path.is_dir() else None


def summarize_packs_for_operator() -> list[dict[str, Any]]:
    """Short list for CLI / staging doc."""
    return [pk.to_dict() for pk in SAMPLE_WORKSPACE_PACKS.values()]

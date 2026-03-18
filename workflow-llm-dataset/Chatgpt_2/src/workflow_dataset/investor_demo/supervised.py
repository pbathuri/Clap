"""
M51I–M51L: Supervised action demo — simulate-only action card + preview.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from workflow_dataset.action_cards.models import ActionCard, HandoffTarget, TrustRequirement
from workflow_dataset.action_cards.preview import build_preview
from workflow_dataset.investor_demo.models import SupervisedActionDemo


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def build_supervised_action_demo(repo_root: Path | str | None = None) -> SupervisedActionDemo:
    """
    Deterministic demo card: prefill a safe mission-control command (no execution).
    """
    root = _root(repo_root)
    now = datetime.now(timezone.utc).isoformat()[:19] + "Z"
    card = ActionCard(
        card_id="investor_demo_supervised_prefill_mc",
        title="Review mission control (demo)",
        description="Investor-safe: prefills a read-only command to show product state.",
        source_type="investor_demo",
        source_ref="m51_demo",
        handoff_target=HandoffTarget.PREFILL_COMMAND,
        handoff_params={
            "command": "workflow-dataset mission-control",
            "hint": "Read-only aggregate; no writes.",
        },
        trust_requirement=TrustRequirement.SIMULATE_ONLY,
        reversible=True,
        created_utc=now,
    )
    preview = build_preview(card)
    approval_next = (
        "If this were an execution path: operator would approve in review-studio or agent-loop. "
        "This demo only prefills `workflow-dataset mission-control` — still read-only."
    )
    return SupervisedActionDemo(
        card_id=card.card_id,
        title=card.title,
        description=card.description,
        preview={
            "what_would_happen": preview.what_would_happen,
            "trust_note": preview.trust_note,
            "command_hint": preview.command_hint,
            "approval_required": preview.approval_required,
            "simulate_first": preview.simulate_first,
        },
        what_happens_on_approval=approval_next,
        trust_posture="simulate_only",
    )

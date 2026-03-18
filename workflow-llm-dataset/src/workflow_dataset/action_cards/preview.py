"""
M32I–M32L: Action preview — what would happen, trust note, command hint.
"""

from __future__ import annotations

from workflow_dataset.action_cards.models import ActionCard, ActionPreview, HandoffTarget, TrustRequirement


def build_preview(card: ActionCard) -> ActionPreview:
    """Build human-readable preview for an action card. No execution."""
    summary = card.title or card.card_id
    what = ""
    cmd = ""
    approval = False
    simulate_first = True

    if card.handoff_target == HandoffTarget.PREFILL_COMMAND:
        cmd = card.handoff_params.get("command", "workflow-dataset")
        what = f"Would prefill or run: {cmd}. Params: {card.handoff_params.get('hint', 'see handoff_params')}"
    elif card.handoff_target == HandoffTarget.COMPILE_PLAN:
        goal = card.handoff_params.get("goal", card.handoff_params.get("plan_ref", ""))
        what = f"Would compile a plan for: {goal[:80]}. Mode: {card.handoff_params.get('mode', 'simulate')}."
        cmd = "planner compile --goal \"...\""
        simulate_first = (card.handoff_params.get("mode") == "simulate")
    elif card.handoff_target == HandoffTarget.QUEUE_SIMULATED:
        plan_ref = card.handoff_params.get("plan_ref", "")
        what = f"Would queue a simulated run for plan_ref={plan_ref}. Action will appear in approval queue; no execution until approved."
        cmd = "agent-loop status  (then approve to execute)"
        approval = True
        simulate_first = True
    elif card.handoff_target == HandoffTarget.APPROVAL_STUDIO:
        what = "Would open approval queue / review studio. You can then approve or reject the pending action."
        cmd = "review-studio inbox  or  agent-loop status"
        approval = True
    elif card.handoff_target == HandoffTarget.CREATE_DRAFT:
        sug_id = card.handoff_params.get("suggestion_id", "")
        what = f"Would create a draft artifact from suggestion {sug_id} in the sandbox (data/local/workspaces). No real project files changed."
        cmd = "assist materialize ... (with suggestion id)"
    elif card.handoff_target == HandoffTarget.OPEN_VIEW:
        view_id = card.handoff_params.get("view_id", "")
        what = f"Would open view: {view_id}. No execution."
    elif card.handoff_target == HandoffTarget.EXECUTOR_RUN:
        what = "Would queue executor run. Approval required before real execution; simulate mode available."
        cmd = "executor run ... or agent-loop approve"
        approval = card.trust_requirement == TrustRequirement.APPROVAL_REQUIRED
    else:
        what = f"Handoff target: {card.handoff_target.value}. Params: {list(card.handoff_params.keys())}"

    trust_note = ""
    if card.trust_requirement == TrustRequirement.APPROVAL_REQUIRED:
        trust_note = "Approval required before real execution. Use approval queue or review studio."
    elif card.trust_requirement == TrustRequirement.SIMULATE_ONLY:
        trust_note = "Simulate-only; no real execution. Safe to run."
    elif card.trust_requirement == TrustRequirement.TRUSTED_PATH:
        trust_note = "Trusted path; still requires explicit execute."
    if card.blocked_reason:
        trust_note = (trust_note + " BLOCKED: " + card.blocked_reason).strip()

    return ActionPreview(
        card_id=card.card_id,
        summary=summary,
        what_would_happen=what,
        trust_note=trust_note,
        command_hint=cmd,
        approval_required=approval,
        simulate_first=simulate_first,
    )

"""
M36L.1: Carry-forward policy — classify items into urgent, optional, automated_follow_up.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

try:
    from workflow_dataset.utils.hashes import stable_id
except Exception:
    def stable_id(*parts: str, prefix: str = "") -> str:
        import hashlib
        return prefix + hashlib.sha256("".join(str(p) for p in parts).encode()).hexdigest()[:14]

from workflow_dataset.continuity_engine.models import (
    CarryForwardItem,
    CarryForwardPolicyOutput,
    CARRY_FORWARD_CLASS_URGENT,
    CARRY_FORWARD_CLASS_OPTIONAL,
    CARRY_FORWARD_CLASS_AUTOMATED_FOLLOW_UP,
)


def _classify_item(item: Any) -> str:
    """
    Classify a single queue item into urgent | optional | automated_follow_up.
    First-draft rules: approval_queue+high/urgent or blocked -> urgent;
    routing_target automation_follow_up or automation_inbox result -> automated_follow_up;
    else optional.
    """
    source = (getattr(item, "source_subsystem", None) or getattr(item, "source", "") or "")
    if hasattr(source, "value"):
        source = source.value
    source = str(source).lower()
    priority = str(getattr(item, "priority", "medium") or "medium").lower()
    actionability = str(getattr(item, "actionability_class", "") or "")
    if hasattr(getattr(item, "actionability_class", None), "value"):
        actionability = getattr(item.actionability_class, "value", actionability)
    actionability = actionability.lower()
    routing = str(getattr(item, "routing_target", "") or "").lower()
    blocked = bool(getattr(item, "blocked_reason", "") or "blocked" in actionability)

    if blocked or actionability == "blocked":
        return CARRY_FORWARD_CLASS_URGENT
    if source == "approval_queue" and priority in ("urgent", "high"):
        return CARRY_FORWARD_CLASS_URGENT
    if source == "automation_inbox" or "automation" in source:
        if routing == "automation_follow_up" or priority == "low":
            return CARRY_FORWARD_CLASS_AUTOMATED_FOLLOW_UP
        if priority in ("urgent", "high"):
            return CARRY_FORWARD_CLASS_URGENT
    if routing == "automation_follow_up":
        return CARRY_FORWARD_CLASS_AUTOMATED_FOLLOW_UP
    return CARRY_FORWARD_CLASS_OPTIONAL


def _item_to_carry_forward(item: Any, now: str, carry_class: str) -> CarryForwardItem:
    """Build CarryForwardItem from queue item with carry_forward_class set."""
    label = (getattr(item, "label", "") or getattr(item, "summary", "") or "")[:100]
    item_id = getattr(item, "item_id", "") or getattr(item, "source_ref", "")
    ref = getattr(item, "source_ref", "") or item_id
    return CarryForwardItem(
        item_id=stable_id("cf", label, now, prefix="cf_"),
        kind="unresolved",
        carry_forward_class=carry_class,
        label=label,
        ref=ref,
        command="workflow-dataset queue view",
        created_at_utc=now,
        priority=getattr(item, "priority", "medium") or "medium",
    )


def apply_carry_forward_policy(
    queue_items: list[Any],
    repo_root: Path | str | None = None,
    limit_per_class: int = 10,
) -> CarryForwardPolicyOutput:
    """
    Classify queue items into urgent, optional, automated_follow_up.
    Returns CarryForwardPolicyOutput with rationale_lines and items with carry_forward_class set.
    """
    now = utc_now_iso()
    urgent: list[CarryForwardItem] = []
    optional: list[CarryForwardItem] = []
    automated: list[CarryForwardItem] = []
    rationale: list[str] = []

    for item in queue_items[: limit_per_class * 3]:
        carry_class = _classify_item(item)
        cf = _item_to_carry_forward(item, now, carry_class)
        if carry_class == CARRY_FORWARD_CLASS_URGENT:
            if len(urgent) < limit_per_class:
                urgent.append(cf)
        elif carry_class == CARRY_FORWARD_CLASS_AUTOMATED_FOLLOW_UP:
            if len(automated) < limit_per_class:
                automated.append(cf)
        else:
            if len(optional) < limit_per_class:
                optional.append(cf)

    if urgent:
        rationale.append(f"{len(urgent)} urgent carry-forward (approvals/blocked).")
    if automated:
        rationale.append(f"{len(automated)} automated follow-up item(s).")
    if optional:
        rationale.append(f"{len(optional)} optional carry-forward.")
    if not rationale:
        rationale.append("No carry-forward items.")

    return CarryForwardPolicyOutput(
        urgent_items=urgent,
        optional_items=optional,
        automated_follow_up_items=automated,
        rationale_lines=rationale,
        generated_at_utc=now,
    )


def build_next_day_operating_recommendation(
    policy_output: CarryForwardPolicyOutput,
    tomorrow_start: str = "",
    repo_root: Path | str | None = None,
) -> tuple[str, str, list[str]]:
    """
    From policy output, return (first_action_label, first_action_command, rationale_lines).
    Urgent count > 0 -> review first; else automated > 0 -> optional review; else morning flow.
    """
    u = len(policy_output.urgent_items)
    o = len(policy_output.optional_items)
    a = len(policy_output.automated_follow_up_items)
    rationale = list(policy_output.rationale_lines)
    if u > 0:
        label = "Review urgent carry-forward"
        command = "workflow-dataset continuity carry-forward"
        rationale.insert(0, f"Start with {u} urgent item(s); run carry-forward then queue.")
    elif a > 0 and (a >= o or o == 0):
        label = "Check automated follow-up"
        command = "workflow-dataset automation-inbox list"
        rationale.insert(0, f"{a} automated follow-up item(s) in inbox.")
    elif o > 0:
        label = "Review optional carry-forward"
        command = "workflow-dataset continuity carry-forward"
        rationale.insert(0, f"{o} optional item(s) carried forward.")
    else:
        label = "Run morning flow"
        command = "workflow-dataset continuity morning"
        rationale.insert(0, "No carry-forward; start with morning brief.")
    if tomorrow_start:
        rationale.append(f"Context: {tomorrow_start}")
    return label, command, rationale

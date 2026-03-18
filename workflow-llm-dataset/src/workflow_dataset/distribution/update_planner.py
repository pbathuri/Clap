"""
M24R–M24U: Update planner — compare current vs desired state, show what would change, risks, stage plan.
No execution; local-safe and reversible where possible.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()


@dataclass
class UpdatePlan:
    """Staged update plan: steps, risks, reversible flag. No execution."""
    plan_id: str
    generated_at: str = ""
    current_state_summary: dict[str, Any] = field(default_factory=dict)
    desired_state_summary: dict[str, Any] = field(default_factory=dict)
    steps: list[dict[str, Any]] = field(default_factory=list)  # [{action, detail, reversible}]
    risks: list[str] = field(default_factory=list)
    reversible_overall: bool = True


def _repo_root(root: Path | str | None) -> Path:
    if root is not None:
        return Path(root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def build_update_plan(
    repo_root: Path | str | None = None,
    desired_state: dict[str, Any] | None = None,
    current_state: dict[str, Any] | None = None,
) -> UpdatePlan:
    """
    Compare current install state vs desired state; produce staged update plan.
    If desired_state is None, uses current profile as desired (no-op plan). No execution.
    """
    root = _repo_root(repo_root)
    plan = UpdatePlan(plan_id="update_plan", generated_at=utc_now_iso())
    if current_state is None:
        try:
            from workflow_dataset.local_deployment.profile import build_local_deployment_profile
            plan.current_state_summary = build_local_deployment_profile(repo_root=root)
        except Exception:
            plan.current_state_summary = {}
    else:
        plan.current_state_summary = current_state
    plan.desired_state_summary = desired_state or plan.current_state_summary
    # First-draft: derive steps from diff-like logic (readiness vs desired readiness, profile keys)
    cur_r = (plan.current_state_summary.get("readiness") or {}).get("ready_for_first_real_user_install")
    des_r = (plan.desired_state_summary.get("readiness") or {}).get("ready_for_first_real_user_install") if plan.desired_state_summary else cur_r
    if des_r and not cur_r:
        plan.steps.append({"action": "meet_readiness", "detail": "Fix prerequisites until ready_for_first_real_user_install is true.", "reversible": True})
        plan.risks.append("Readiness checks may require env or config changes.")
    if not plan.steps:
        plan.steps.append({"action": "none", "detail": "Current state matches or no desired state specified.", "reversible": True})
    plan.reversible_overall = all(s.get("reversible", True) for s in plan.steps)
    return plan


def format_update_plan(plan: UpdatePlan) -> str:
    """Human-readable update plan."""
    lines = [
        "=== Update plan (staged; no execution) ===",
        "",
        f"Plan id: {plan.plan_id}  Generated: {plan.generated_at}",
        "",
        "[Steps]",
    ]
    for s in plan.steps:
        lines.append(f"  - {s.get('action', '')}: {s.get('detail', '')}  (reversible={s.get('reversible', True)})")
    lines.append("")
    lines.append("[Risks]")
    for r in plan.risks:
        lines.append(f"  - {r}")
    if not plan.risks:
        lines.append("  (none)")
    lines.append("")
    lines.append(f"Reversible overall: {plan.reversible_overall}")
    lines.append("(Operator-controlled. Run deploy/install steps manually if desired.)")
    return "\n".join(lines)

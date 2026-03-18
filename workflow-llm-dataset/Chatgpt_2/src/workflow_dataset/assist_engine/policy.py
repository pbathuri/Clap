"""
M32H.1: Apply quiet hours, focus-safe, and interruptibility policy.

Evaluates whether to show a suggestion or hold it back; returns clear hold_back_reason for explanations.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from workflow_dataset.assist_engine.models import AssistSuggestion
from workflow_dataset.assist_engine.policy_models import (
    AssistPolicyConfig,
    QuietHoursWindow,
    FocusSafeRule,
    InterruptibilityRule,
)
from workflow_dataset.assist_engine.store import get_assist_engine_root

POLICY_FILE = "policy.yaml"


def load_policy(repo_root: Path | str | None = None) -> AssistPolicyConfig:
    """Load policy from data/local/assist_engine/policy.yaml; return defaults if missing."""
    root = get_assist_engine_root(repo_root)
    path = root / POLICY_FILE
    if not path.exists():
        return AssistPolicyConfig()
    try:
        import yaml
        raw = path.read_text(encoding="utf-8")
        data = yaml.safe_load(raw) or {}
    except Exception:
        return AssistPolicyConfig()
    # Parse nested structures
    quiet = []
    for w in data.get("quiet_hours", []):
        if isinstance(w, dict):
            quiet.append(QuietHoursWindow(**w))
        else:
            quiet.append(QuietHoursWindow())
    focus = data.get("focus_safe")
    if isinstance(focus, dict):
        focus_safe = FocusSafeRule(**focus)
    else:
        focus_safe = FocusSafeRule()
    rules = []
    for r in data.get("interruptibility_rules", []):
        if isinstance(r, dict):
            rules.append(InterruptibilityRule(**r))
    return AssistPolicyConfig(
        quiet_hours=quiet,
        focus_safe=focus_safe,
        interruptibility_rules=rules,
        default_hold_back=bool(data.get("default_hold_back", False)),
    )


def _parse_hhmm(s: str) -> tuple[int, int]:
    """Parse HH:MM or H:MM to (hour, minute)."""
    s = (s or "00:00").strip()
    if ":" in s:
        a, b = s.split(":", 1)
        return int(a.strip() or 0), int(b.strip() or 0)
    return 0, 0


def _time_in_window(now: datetime, window: QuietHoursWindow) -> bool:
    """True if now (UTC) falls inside the quiet window. Handles overnight (e.g. 22:00–07:00)."""
    sh, sm = _parse_hhmm(window.start_utc)
    eh, em = _parse_hhmm(window.end_utc)
    now_minutes = now.hour * 60 + now.minute
    start_minutes = sh * 60 + sm
    end_minutes = eh * 60 + em
    if start_minutes <= end_minutes:
        return start_minutes <= now_minutes < end_minutes
    # Overnight: e.g. 22:00–07:00 -> now in [22:00, 24:00) or [0, 7:00)
    return now_minutes >= start_minutes or now_minutes < end_minutes


def _evaluate_quiet_hours(policy: AssistPolicyConfig, now_utc: datetime) -> str | None:
    """If inside quiet hours, return hold-back reason; else None."""
    for w in policy.quiet_hours:
        if _time_in_window(now_utc, w):
            label = w.description or "Quiet hours"
            return f"{label} (UTC {w.start_utc}–{w.end_utc})"
    return None


def _evaluate_focus_safe(
    policy: AssistPolicyConfig,
    suggestion: AssistSuggestion,
    focus_safe_active: bool,
) -> str | None:
    """If focus-safe is active and suggestion exceeds limits, return hold-back reason."""
    rule = policy.focus_safe
    if not rule.enabled or not focus_safe_active:
        return None
    if suggestion.interruptiveness_score > rule.max_interruptiveness:
        return (
            f"Focus-safe: suggestion interruptiveness {suggestion.interruptiveness_score:.2f} "
            f"exceeds max {rule.max_interruptiveness:.2f}"
        )
    if suggestion.confidence < rule.min_confidence:
        return (
            f"Focus-safe: suggestion confidence {suggestion.confidence:.2f} "
            f"below min {rule.min_confidence:.2f}"
        )
    return None


def _match_rule(rule: InterruptibilityRule, work_mode: str, project_id: str, trust_level: str) -> bool:
    """True if context matches this rule (wildcard * matches any)."""
    w = (rule.work_mode or "*").strip().lower()
    p = (rule.project_id or "*").strip()
    t = (rule.trust_level or "*").strip().lower()
    if w != "*" and w != (work_mode or "").lower():
        return False
    if p != "*" and p != (project_id or ""):
        return False
    if t != "*" and t != (trust_level or "").lower():
        return False
    return True


def _evaluate_interruptibility(
    policy: AssistPolicyConfig,
    suggestion: AssistSuggestion,
    work_mode: str,
    project_id: str,
    trust_level: str,
) -> str | None:
    """If a matching rule says hold back or caps interruptiveness, return reason."""
    for rule in policy.interruptibility_rules:
        if not _match_rule(rule, work_mode, project_id, trust_level):
            continue
        if not rule.allow_suggestions:
            reason = rule.hold_back_reason_template or "Interruptibility policy (no suggestions in this context)"
            return reason.format(project_id=project_id or "", work_mode=work_mode or "", trust_level=trust_level or "")
        if suggestion.interruptiveness_score > rule.max_interruptiveness:
            return (
                f"Interruptibility: in this context (work_mode={work_mode}, project={project_id}) "
                f"max interruptiveness is {rule.max_interruptiveness:.2f}; suggestion has {suggestion.interruptiveness_score:.2f}"
            )
    if policy.default_hold_back:
        return "Interruptibility: no matching allow rule (default hold back)"
    return None


def apply_policy(
    suggestion: AssistSuggestion,
    repo_root: Path | str | None = None,
    *,
    now_utc: datetime | None = None,
    work_mode: str = "",
    project_id: str = "",
    trust_level: str = "",
    focus_safe_active: bool = False,
) -> tuple[bool, str]:
    """
    Decide whether to show the suggestion. Returns (allow, hold_back_reason).
    If allow is False, hold_back_reason is a clear human-readable explanation for why it was held back.
    """
    policy = load_policy(repo_root=repo_root)
    now = now_utc or datetime.now(timezone.utc)

    reason = _evaluate_quiet_hours(policy, now)
    if reason:
        return False, reason

    reason = _evaluate_focus_safe(policy, suggestion, focus_safe_active)
    if reason:
        return False, reason

    reason = _evaluate_interruptibility(
        policy, suggestion,
        work_mode=work_mode,
        project_id=project_id,
        trust_level=trust_level,
    )
    if reason:
        return False, reason

    return True, ""

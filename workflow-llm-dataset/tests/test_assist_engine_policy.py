"""
M32H.1: Tests for quiet hours, focus-safe suppression, interruptibility policy,
and held-back suggestion explanations.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from workflow_dataset.assist_engine.models import AssistSuggestion, SuggestionReason, TriggeringContext
from workflow_dataset.assist_engine.policy import (
    load_policy,
    apply_policy,
)
from workflow_dataset.assist_engine.policy_models import (
    AssistPolicyConfig,
    QuietHoursWindow,
    FocusSafeRule,
    InterruptibilityRule,
)
from workflow_dataset.assist_engine.store import save_suggestion, load_suggestion, get_assist_engine_root
from workflow_dataset.assist_engine.explain import explain_suggestion


def _suggestion(
    suggestion_id: str = "sug_policy_test",
    confidence: float = 0.8,
    interruptiveness_score: float = 0.4,
) -> AssistSuggestion:
    return AssistSuggestion(
        suggestion_id=suggestion_id,
        suggestion_type="next_step",
        title="Test",
        description="Test suggestion",
        reason=SuggestionReason(title="Reason", description="", evidence=[]),
        triggering_context=TriggeringContext(source="test", summary="", signals=[]),
        confidence=confidence,
        usefulness_score=0.7,
        interruptiveness_score=interruptiveness_score,
        status="pending",
        created_utc="2025-03-16T12:00:00Z",
        updated_utc="2025-03-16T12:00:00Z",
    )


def test_load_policy_empty(tmp_path: Path) -> None:
    policy = load_policy(repo_root=tmp_path)
    assert isinstance(policy, AssistPolicyConfig)
    assert policy.quiet_hours == []
    assert policy.focus_safe.enabled is False


def test_load_policy_with_yaml(tmp_path: Path) -> None:
    root = get_assist_engine_root(tmp_path)
    root.mkdir(parents=True, exist_ok=True)
    path = root / "policy.yaml"
    path.write_text("""
quiet_hours:
  - start_utc: "23:00"
    end_utc: "06:00"
    description: "Night"
focus_safe:
  enabled: true
  max_interruptiveness: 0.3
  min_confidence: 0.8
interruptibility_rules:
  - work_mode: focused
    project_id: "*"
    allow_suggestions: true
    max_interruptiveness: 0.2
""", encoding="utf-8")
    policy = load_policy(repo_root=tmp_path)
    assert len(policy.quiet_hours) == 1
    assert policy.quiet_hours[0].start_utc == "23:00"
    assert policy.focus_safe.enabled is True
    assert policy.focus_safe.max_interruptiveness == 0.3
    assert len(policy.interruptibility_rules) == 1


def test_apply_policy_allow_by_default(tmp_path: Path) -> None:
    s = _suggestion(interruptiveness_score=0.2, confidence=0.9)
    allow, reason = apply_policy(s, repo_root=tmp_path)
    assert allow is True
    assert reason == ""


def test_apply_policy_focus_safe_holds_back(tmp_path: Path) -> None:
    root = get_assist_engine_root(tmp_path)
    root.mkdir(parents=True, exist_ok=True)
    (root / "policy.yaml").write_text("""
focus_safe:
  enabled: true
  max_interruptiveness: 0.3
  min_confidence: 0.7
""", encoding="utf-8")
    s = _suggestion(interruptiveness_score=0.5, confidence=0.8)
    allow, reason = apply_policy(s, repo_root=tmp_path, focus_safe_active=True)
    assert allow is False
    assert "Focus-safe" in reason
    assert "0.5" in reason or "0.50" in reason


def test_apply_policy_quiet_hours(tmp_path: Path) -> None:
    root = get_assist_engine_root(tmp_path)
    root.mkdir(parents=True, exist_ok=True)
    (root / "policy.yaml").write_text("""
quiet_hours:
  - start_utc: "00:00"
    end_utc: "23:59"
    description: "All day quiet"
""", encoding="utf-8")
    s = _suggestion()
    # Use a time inside the window (e.g. noon UTC)
    noon = datetime(2025, 3, 16, 12, 0, 0, tzinfo=timezone.utc)
    allow, reason = apply_policy(s, repo_root=tmp_path, now_utc=noon)
    assert allow is False
    assert "quiet" in reason.lower() or "00:00" in reason


def test_apply_policy_interruptibility_deny(tmp_path: Path) -> None:
    root = get_assist_engine_root(tmp_path)
    root.mkdir(parents=True, exist_ok=True)
    (root / "policy.yaml").write_text("""
interruptibility_rules:
  - work_mode: focused
    project_id: main_app
    trust_level: "*"
    allow_suggestions: false
    hold_back_reason_template: "Quiet focus mode for project {project_id}"
""", encoding="utf-8")
    s = _suggestion()
    allow, reason = apply_policy(
        s, repo_root=tmp_path,
        work_mode="focused",
        project_id="main_app",
        trust_level="",
    )
    assert allow is False
    assert "main_app" in reason or "focus" in reason.lower()


def test_held_back_explanation_in_explain(tmp_path: Path) -> None:
    s = _suggestion("sug_held")
    s.status = "held_back"
    s.held_back_reason = "Night quiet (UTC 22:00–07:00)"
    save_suggestion(s, repo_root=tmp_path)
    ex = explain_suggestion("sug_held", repo_root=tmp_path)
    assert ex.get("held_back") is True
    assert "held_back_explanation" in ex
    assert "22:00" in ex["held_back_explanation"] or "quiet" in ex["held_back_explanation"].lower()


def test_policy_models_defaults() -> None:
    rule = InterruptibilityRule(work_mode="focused", allow_suggestions=False)
    assert rule.hold_back_reason_template == ""
    cfg = AssistPolicyConfig()
    assert cfg.default_hold_back is False

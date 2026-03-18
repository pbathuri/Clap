"""M51L.1: Presenter mode + 5-minute script + degraded narrative bridge."""

from __future__ import annotations

from pathlib import Path

from workflow_dataset.investor_demo.models import DegradedDemoWarning
from workflow_dataset.investor_demo.degraded_narrative import degraded_narrative_bridge
from workflow_dataset.investor_demo.five_minute_script import (
    build_five_minute_demo_script,
    beat_for_stage,
    format_script_compact_text,
)
from workflow_dataset.investor_demo.presenter_mode import (
    set_presenter_mode,
    load_presenter_config,
    build_presenter_mode_view,
    format_presenter_mode_text,
    presenter_config_path,
)
from workflow_dataset.investor_demo.session_store import start_demo_session
from workflow_dataset.investor_demo.models import DemoNarrativeStage


def test_degraded_narrative_bridge_empty() -> None:
    assert degraded_narrative_bridge([]) == ""


def test_degraded_narrative_bridge_non_empty() -> None:
    w = [DegradedDemoWarning("a", "Env not ok", "t")]
    s = degraded_narrative_bridge(w)
    assert "transparency" in s.lower() or "degraded" in s.lower() or "five-minute" in s
    assert "Env not ok" in s or "Main signal" in s


def test_five_minute_script_eight_beats_300s() -> None:
    script = build_five_minute_demo_script()
    assert len(script.beats) == 8
    assert 280 <= script.total_target_seconds <= 320
    assert script.beats[0].stage_id == DemoNarrativeStage.STARTUP_READINESS.value
    assert script.beats[-1].stage_id == DemoNarrativeStage.CLOSING_MISSION_CONTROL_SUMMARY.value
    assert all(b.if_degraded_say for b in script.beats)


def test_beat_for_stage() -> None:
    b = beat_for_stage(DemoNarrativeStage.ARTIFACT_GENERATION.value)
    assert b is not None
    assert "first-value" in b.click_or_run or "artifact" in b.say.lower()


def test_format_script_contains_degraded_line() -> None:
    text = format_script_compact_text()
    assert "IF DEGRADED" in text or "if_degraded" in text.lower()
    assert "5-minute" in text.lower() or "300" in text


def test_presenter_mode_toggle(tmp_path: Path) -> None:
    cfg = set_presenter_mode(True, repo_root=tmp_path)
    assert cfg.enabled
    assert presenter_config_path(tmp_path).exists()
    cfg2 = load_presenter_config(tmp_path)
    assert cfg2.enabled
    set_presenter_mode(False, repo_root=tmp_path)
    assert not load_presenter_config(tmp_path).enabled


def test_presenter_mode_view(tmp_path: Path) -> None:
    start_demo_session(repo_root=tmp_path, vertical_id="v")
    set_presenter_mode(True, repo_root=tmp_path)
    view = build_presenter_mode_view(tmp_path)
    assert view.current_stage_id == DemoNarrativeStage.STARTUP_READINESS.value
    assert view.current_beat is not None
    text = format_presenter_mode_text(view)
    assert "Presenter mode" in text
    assert "SHOW:" in text or "RUN:" in text

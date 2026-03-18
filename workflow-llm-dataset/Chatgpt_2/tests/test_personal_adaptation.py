"""M31I–M31L: Tests for personal adaptation — preference/style candidates, evidence, apply, explain."""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.personal_adaptation.models import (
    PreferenceCandidate,
    StylePatternCandidate,
    AcceptedPreferenceUpdate,
    REVIEW_STATUS_PENDING,
    REVIEW_STATUS_ACCEPTED,
    AFFECTED_SURFACES,
)
from workflow_dataset.personal_adaptation.candidates import (
    generate_preference_candidates,
    generate_style_candidates,
)
from workflow_dataset.personal_adaptation.store import (
    save_candidate,
    get_candidate,
    list_candidates,
    accept_candidate,
    list_accepted,
    get_adaptation_dir,
)
from workflow_dataset.personal_adaptation.explain import explain_preference, format_explain_output
from workflow_dataset.personal_adaptation.apply import apply_accepted_preference


def test_preference_candidate_model() -> None:
    c = PreferenceCandidate(
        candidate_id="pref_1",
        key="output_style.job1",
        proposed_value="bullet",
        confidence=0.8,
        evidence=["Correction: output_style_correction"],
        source="corrections",
        affected_surface="specialization_output_style",
        review_status=REVIEW_STATUS_PENDING,
    )
    d = c.to_dict()
    assert d["key"] == "output_style.job1"
    assert d["confidence"] == 0.8
    assert PreferenceCandidate.from_dict(d).candidate_id == c.candidate_id


def test_style_pattern_candidate_model() -> None:
    c = StylePatternCandidate(
        candidate_id="style_1",
        pattern_type="naming_style",
        description="Revision naming",
        confidence=0.7,
        evidence=["pattern A", "pattern B"],
        affected_surface="output_framing",
        review_status=REVIEW_STATUS_PENDING,
    )
    d = c.to_dict()
    assert d["pattern_type"] == "naming_style"
    assert StylePatternCandidate.from_dict(d).candidate_id == c.candidate_id


def test_generate_preference_candidates_returns_list(tmp_path: Path) -> None:
    out = generate_preference_candidates(repo_root=tmp_path)
    assert isinstance(out, list)


def test_generate_style_candidates_returns_list(tmp_path: Path) -> None:
    out = generate_style_candidates(repo_root=tmp_path)
    assert isinstance(out, list)


def test_save_and_get_candidate(tmp_path: Path) -> None:
    c = PreferenceCandidate(
        candidate_id="pref_test_1",
        key="test.key",
        proposed_value="value",
        confidence=0.9,
        evidence=[],
        affected_surface="pack_defaults",
        review_status=REVIEW_STATUS_PENDING,
    )
    save_candidate(c, repo_root=tmp_path)
    loaded = get_candidate("pref_test_1", tmp_path)
    assert loaded is not None
    assert loaded.key == c.key
    assert get_candidate("nonexistent", tmp_path) is None


def test_list_candidates(tmp_path: Path) -> None:
    c = PreferenceCandidate(candidate_id="pref_list_1", key="k", proposed_value="v", confidence=0.5, affected_surface="output_framing", review_status=REVIEW_STATUS_PENDING)
    save_candidate(c, repo_root=tmp_path)
    items = list_candidates(repo_root=tmp_path, kind="preference", limit=10)
    assert len(items) >= 1
    assert items[0].get("key") == "k"
    items_both = list_candidates(repo_root=tmp_path, kind=None, limit=10)
    assert len(items_both) >= 1


def test_accept_candidate(tmp_path: Path) -> None:
    c = PreferenceCandidate(candidate_id="pref_accept_1", key="accept.key", proposed_value="val", confidence=0.8, affected_surface="output_framing", review_status=REVIEW_STATUS_PENDING)
    save_candidate(c, repo_root=tmp_path)
    update = accept_candidate("pref_accept_1", repo_root=tmp_path)
    assert update is not None
    assert update.candidate_id == "pref_accept_1"
    assert update.candidate_type == "preference"
    accepted_list = list_accepted(repo_root=tmp_path, limit=5)
    assert len(accepted_list) >= 1
    reloaded = get_candidate("pref_accept_1", tmp_path)
    assert reloaded is not None and reloaded.review_status == REVIEW_STATUS_ACCEPTED


def test_explain_preference(tmp_path: Path) -> None:
    c = PreferenceCandidate(candidate_id="pref_explain_1", key="explain.key", proposed_value="x", confidence=0.6, evidence=["e1", "e2"], source="corrections", affected_surface="output_framing")
    save_candidate(c, repo_root=tmp_path)
    explain_dict = explain_preference("pref_explain_1", repo_root=tmp_path)
    assert "error" not in explain_dict
    assert explain_dict["key_or_pattern"] == "explain.key"
    assert "e1" in explain_dict.get("evidence", []) or "e2" in explain_dict.get("evidence", [])
    text = format_explain_output(explain_dict)
    assert "explain.key" in text
    assert "Evidence" in text
    missing = explain_preference("nonexistent", repo_root=tmp_path)
    assert missing.get("error") is not None


def test_apply_accepted_preference_not_found(tmp_path: Path) -> None:
    result = apply_accepted_preference("upd_nonexistent_123", repo_root=tmp_path)
    assert result["applied"] is False
    assert "not found" in result.get("message", "").lower()


def test_affected_surfaces_constant() -> None:
    assert "pack_defaults" in AFFECTED_SURFACES
    assert "output_framing" in AFFECTED_SURFACES
    assert "specialization_output_style" in AFFECTED_SURFACES


# ----- M31L.1 Profile presets + behavior deltas -----
from workflow_dataset.personal_adaptation.models import BehaviorDelta, PersonalProfilePreset
from workflow_dataset.personal_adaptation.behavior_delta import (
    build_behavior_delta_for_candidate,
    build_behavior_delta_for_preset,
    format_behavior_delta_output,
)
from workflow_dataset.personal_adaptation.presets import save_preset, load_preset, list_presets, create_preset
from workflow_dataset.personal_adaptation.store import get_presets_dir


def test_behavior_delta_model() -> None:
    d = BehaviorDelta(
        surface="specialization_output_style",
        key_or_target="weekly_report",
        before_value="paragraph",
        after_value="bullet",
        human_summary="Packs: output style will change to bullet.",
    )
    assert d.surface == "specialization_output_style"
    assert d.before_value == "paragraph"
    assert d.to_dict()["human_summary"]


def test_personal_profile_preset_model(tmp_path: Path) -> None:
    p = PersonalProfilePreset(
        preset_id="preset_1",
        name="Report style",
        description="Output and path prefs for reports",
        candidate_ids=["pref_1", "pref_2"],
        created_utc="2025-01-01T00:00:00",
        updated_utc="2025-01-01T00:00:00",
    )
    save_preset(p, repo_root=tmp_path)
    loaded = load_preset("preset_1", tmp_path)
    assert loaded is not None
    assert loaded.name == "Report style"
    assert len(loaded.candidate_ids) == 2
    assert load_preset("nonexistent", tmp_path) is None


def test_list_presets(tmp_path: Path) -> None:
    p = PersonalProfilePreset(preset_id="preset_list_1", name="List test", candidate_ids=["a", "b"])
    save_preset(p, repo_root=tmp_path)
    items = list_presets(repo_root=tmp_path)
    assert len(items) >= 1
    assert items[0].get("name") == "List test"
    assert items[0].get("candidate_count") == 2


def test_create_preset(tmp_path: Path) -> None:
    preset = create_preset("My preset", candidate_ids=["pref_a", "pref_b"], description="Two prefs", repo_root=tmp_path)
    assert preset.preset_id.startswith("preset_")
    assert preset.name == "My preset"
    assert len(preset.candidate_ids) == 2
    loaded = load_preset(preset.preset_id, tmp_path)
    assert loaded is not None


def test_build_behavior_delta_for_candidate(tmp_path: Path) -> None:
    c = PreferenceCandidate(
        candidate_id="pref_delta_1",
        key="output_framing.report",
        proposed_value="bullet",
        confidence=0.8,
        affected_surface="output_framing",
        review_status=REVIEW_STATUS_PENDING,
    )
    save_candidate(c, repo_root=tmp_path)
    deltas = build_behavior_delta_for_candidate("pref_delta_1", repo_root=tmp_path)
    assert len(deltas) >= 1
    assert deltas[0].surface == "output_framing"
    assert deltas[0].after_value == "bullet"
    assert deltas[0].human_summary
    assert build_behavior_delta_for_candidate("nonexistent", repo_root=tmp_path) == []


def test_format_behavior_delta_output() -> None:
    deltas = [
        BehaviorDelta("specialization_output_style", "job1", "paragraph", "bullet", "Packs: output style will change to bullet."),
    ]
    text = format_behavior_delta_output(deltas, candidate_id="pref_1")
    assert "Behavior delta" in text
    assert "Before" in text
    assert "After" in text
    assert "bullet" in text


def test_build_behavior_delta_for_preset(tmp_path: Path) -> None:
    c = PreferenceCandidate(candidate_id="pref_for_preset", key="k", proposed_value="v", confidence=0.7, affected_surface="workspace_preset")
    save_candidate(c, repo_root=tmp_path)
    preset = create_preset("Delta preset", candidate_ids=["pref_for_preset"], repo_root=tmp_path)
    deltas = build_behavior_delta_for_preset(preset.preset_id, repo_root=tmp_path)
    assert len(deltas) >= 1
    assert deltas[0].surface == "workspace_preset"
    assert build_behavior_delta_for_preset("nonexistent", repo_root=tmp_path) == []

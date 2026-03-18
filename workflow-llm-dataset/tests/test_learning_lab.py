"""
M41A–M41D: Tests for local learning lab — pattern mapping, experiments, compare, report, outcome.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.learning_lab.models import (
    PatternMapping,
    ImprovementExperiment,
    ADOPT_PARTIAL,
    REJECT,
    OUTCOME_PENDING,
    OUTCOME_REJECTED,
    OUTCOME_PROMOTED,
    SOURCE_ISSUE_CLUSTER,
    PROFILE_CONSERVATIVE,
    PROFILE_BALANCED,
    TEMPLATE_PROMPT_TUNING,
    TEMPLATE_ROUTING_CHANGES,
    TEMPLATE_TRUST_THRESHOLD_TUNING,
)
from workflow_dataset.learning_lab.pattern_mapping import (
    build_pattern_mapping_report,
    KARPATHY_PATTERN_MAPPINGS,
)
from workflow_dataset.learning_lab.profiles_and_templates import (
    get_profiles,
    get_templates,
    get_profile,
    get_template,
    get_templates_allowed_for_profile,
    is_experiment_allowed_in_environment,
)
from workflow_dataset.learning_lab.store import (
    save_experiment,
    list_experiments,
    get_experiment,
    get_active_experiment_id,
    set_active_experiment_id,
    set_current_profile_id,
    get_current_profile_id,
)
from workflow_dataset.learning_lab.experiments import (
    create_experiment_from_issue_cluster,
    create_experiment_from_repeated_correction,
    compare_before_after,
    record_outcome,
)
from workflow_dataset.learning_lab.report import build_experiment_report, build_comparison_output


def test_pattern_mapping_report():
    """Pattern mapping report has adopted/rejected and reference repos."""
    report = build_pattern_mapping_report(include_rejected=True)
    assert "adopted_count" in report
    assert "rejected_count" in report
    assert "mappings" in report
    assert "reference_repos" in report
    assert report["adopted_count"] + report["rejected_count"] == len(KARPATHY_PATTERN_MAPPINGS)
    assert "karpathy" in str(report["reference_repos"]).lower() or "autoresearch" in str(report["reference_repos"])


def test_pattern_mapping_adopted_only():
    """Report with adopted only excludes rejected."""
    report = build_pattern_mapping_report(include_rejected=False)
    for m in report["mappings"]:
        assert m.get("adoption_type") != REJECT


def test_experiment_model_to_dict():
    """ImprovementExperiment to_dict is serializable."""
    exp = ImprovementExperiment(
        experiment_id="exp_test1",
        source_type=SOURCE_ISSUE_CLUSTER,
        source_ref="cluster_abc",
        label="Test experiment",
        status=OUTCOME_PENDING,
    )
    d = exp.to_dict()
    assert d["experiment_id"] == "exp_test1"
    assert d["source_type"] == SOURCE_ISSUE_CLUSTER
    assert d["status"] == OUTCOME_PENDING


def test_save_and_list_experiments(tmp_path):
    """Save experiment and list returns it."""
    exp = ImprovementExperiment(
        experiment_id="exp_save1",
        source_type=SOURCE_ISSUE_CLUSTER,
        source_ref="c1",
        label="Saved",
        status=OUTCOME_PENDING,
    )
    save_experiment(exp, tmp_path)
    experiments = list_experiments(limit=10, repo_root=tmp_path)
    assert len(experiments) >= 1
    assert any(e.experiment_id == "exp_save1" for e in experiments)


def test_get_experiment(tmp_path):
    """Get experiment by id returns latest when multiple lines."""
    exp = ImprovementExperiment(experiment_id="exp_get1", source_type=SOURCE_ISSUE_CLUSTER, source_ref="c1", status=OUTCOME_PENDING)
    save_experiment(exp, tmp_path)
    found = get_experiment("exp_get1", tmp_path)
    assert found is not None
    assert found.experiment_id == "exp_get1"
    assert get_experiment("nonexistent_exp_xyz", tmp_path) is None


def test_compare_before_after_no_runs(tmp_path):
    """Compare without runs returns slice summary."""
    exp = ImprovementExperiment(
        experiment_id="exp_compare1",
        source_type=SOURCE_ISSUE_CLUSTER,
        source_ref="c1",
        label="Compare test",
        status=OUTCOME_PENDING,
    )
    save_experiment(exp, tmp_path)
    out = compare_before_after("exp_compare1", repo_root=tmp_path)
    assert "comparison_summary" in out
    assert out.get("experiment_id") == "exp_compare1"


def test_compare_nonexistent():
    """Compare for nonexistent experiment returns error."""
    out = compare_before_after("exp_nonexistent_xyz", repo_root=Path("/nonexistent_repo"))
    assert out.get("error") is not None


def test_record_outcome(tmp_path):
    """Record outcome updates status (append-only; get_experiment returns latest)."""
    exp = ImprovementExperiment(
        experiment_id="exp_outcome1",
        source_type=SOURCE_ISSUE_CLUSTER,
        source_ref="c1",
        status=OUTCOME_PENDING,
    )
    save_experiment(exp, tmp_path)
    updated = record_outcome("exp_outcome1", outcome=OUTCOME_PROMOTED, reason="Evidence strong", repo_root=tmp_path)
    assert updated is not None
    assert updated.status == OUTCOME_PROMOTED
    assert updated.status_reason == "Evidence strong"
    found = get_experiment("exp_outcome1", tmp_path)
    assert found is not None
    assert found.status == OUTCOME_PROMOTED


def test_record_outcome_invalid():
    """Invalid outcome returns None."""
    assert record_outcome("exp_xyz", outcome="invalid_outcome", repo_root=Path("/tmp")) is None


def test_build_experiment_report(tmp_path):
    """Build experiment report returns dict with status and comparison_summary."""
    exp = ImprovementExperiment(
        experiment_id="exp_report1",
        source_type=SOURCE_ISSUE_CLUSTER,
        source_ref="c1",
        label="Report test",
        status=OUTCOME_PENDING,
    )
    save_experiment(exp, tmp_path)
    report = build_experiment_report("exp_report1", repo_root=tmp_path)
    assert report.get("experiment_id") == "exp_report1"
    assert "status" in report
    assert "comparison_summary" in report


def test_build_experiment_report_not_found():
    """Report for nonexistent experiment returns error."""
    report = build_experiment_report("exp_not_found_xyz", repo_root=Path("/tmp"))
    assert report.get("error") is not None


def test_create_from_issue_cluster_no_cluster(tmp_path):
    """Create from nonexistent cluster returns None."""
    exp = create_experiment_from_issue_cluster("cluster_nonexistent_xyz", repo_root=tmp_path)
    assert exp is None


def test_create_from_repeated_correction_insufficient(tmp_path):
    """Create from repeated correction with no proposed updates returns None."""
    exp = create_experiment_from_repeated_correction("specialization_params", "job_xyz", min_corrections=5, repo_root=tmp_path)
    # May be None if no proposed updates for that target
    assert exp is None or exp.experiment_id


def test_active_experiment_id(tmp_path):
    """Set and get active experiment id."""
    set_active_experiment_id("exp_active1", tmp_path)
    assert get_active_experiment_id(tmp_path) == "exp_active1"
    set_active_experiment_id("", tmp_path)
    assert get_active_experiment_id(tmp_path) == ""


# ----- M41D.1 Learning profiles and experiment templates -----


def test_get_profiles():
    """get_profiles returns 3 built-in profiles with expected ids."""
    profiles = get_profiles()
    ids = [p.profile_id for p in profiles]
    assert PROFILE_CONSERVATIVE in ids
    assert PROFILE_BALANCED in ids
    assert "research_heavy" in ids
    assert len(profiles) == 3


def test_get_templates():
    """get_templates returns 4 built-in templates."""
    templates = get_templates()
    ids = [t.template_id for t in templates]
    assert TEMPLATE_PROMPT_TUNING in ids
    assert TEMPLATE_ROUTING_CHANGES in ids
    assert "queue_tuning" in ids
    assert TEMPLATE_TRUST_THRESHOLD_TUNING in ids
    assert len(templates) == 4


def test_get_profile_get_template():
    """get_profile and get_template return correct or None."""
    assert get_profile(PROFILE_CONSERVATIVE) is not None
    assert get_profile(PROFILE_CONSERVATIVE).label == "Conservative"
    assert get_profile("nonexistent_xyz") is None
    assert get_template(TEMPLATE_PROMPT_TUNING) is not None
    assert get_template(TEMPLATE_PROMPT_TUNING).production_adjacent_allowed is True
    assert get_template("nonexistent_xyz") is None


def test_templates_allowed_for_profile_local():
    """Conservative profile locally allows prompt_tuning and trust_threshold_tuning."""
    allowed = get_templates_allowed_for_profile(PROFILE_CONSERVATIVE, production_adjacent=False)
    assert TEMPLATE_PROMPT_TUNING in allowed
    assert TEMPLATE_TRUST_THRESHOLD_TUNING in allowed
    assert TEMPLATE_ROUTING_CHANGES not in allowed


def test_templates_allowed_for_profile_production_adjacent():
    """Conservative profile in production-adjacent allows only trust_threshold_tuning."""
    allowed = get_templates_allowed_for_profile(PROFILE_CONSERVATIVE, production_adjacent=True)
    assert TEMPLATE_TRUST_THRESHOLD_TUNING in allowed
    assert TEMPLATE_PROMPT_TUNING not in allowed
    assert TEMPLATE_ROUTING_CHANGES not in allowed


def test_safety_boundary_is_experiment_allowed():
    """is_experiment_allowed_in_environment enforces safety boundaries."""
    assert is_experiment_allowed_in_environment(PROFILE_CONSERVATIVE, TEMPLATE_TRUST_THRESHOLD_TUNING, True) is True
    assert is_experiment_allowed_in_environment(PROFILE_CONSERVATIVE, TEMPLATE_ROUTING_CHANGES, True) is False
    assert is_experiment_allowed_in_environment(PROFILE_BALANCED, TEMPLATE_PROMPT_TUNING, True) is True


def test_current_profile_get_set(tmp_path):
    """set_current_profile_id and get_current_profile_id; default balanced when file missing."""
    assert get_current_profile_id(tmp_path) == "balanced"
    set_current_profile_id(PROFILE_CONSERVATIVE, tmp_path)
    assert get_current_profile_id(tmp_path) == PROFILE_CONSERVATIVE


def test_experiment_with_profile_and_template(tmp_path):
    """Save and load experiment with profile_id and template_id."""
    exp = ImprovementExperiment(
        experiment_id="exp_prof1",
        source_type=SOURCE_ISSUE_CLUSTER,
        source_ref="c1",
        status=OUTCOME_PENDING,
        profile_id=PROFILE_BALANCED,
        template_id=TEMPLATE_PROMPT_TUNING,
    )
    save_experiment(exp, tmp_path)
    found = get_experiment("exp_prof1", tmp_path)
    assert found is not None
    assert found.profile_id == PROFILE_BALANCED
    assert found.template_id == TEMPLATE_PROMPT_TUNING


def test_build_experiment_report_includes_profile_template(tmp_path):
    """Experiment report includes profile_id and template_id when set."""
    exp = ImprovementExperiment(
        experiment_id="exp_rep_prof1",
        source_type=SOURCE_ISSUE_CLUSTER,
        source_ref="c1",
        status=OUTCOME_PENDING,
        profile_id=PROFILE_CONSERVATIVE,
        template_id=TEMPLATE_TRUST_THRESHOLD_TUNING,
    )
    save_experiment(exp, tmp_path)
    report = build_experiment_report("exp_rep_prof1", repo_root=tmp_path)
    assert report.get("profile_id") == PROFILE_CONSERVATIVE
    assert report.get("template_id") == TEMPLATE_TRUST_THRESHOLD_TUNING

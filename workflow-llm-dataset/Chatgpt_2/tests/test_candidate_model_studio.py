"""
M42E–M42H: Candidate model studio — candidate creation, dataset slice curation,
lineage/provenance, training path behavior, quarantined handling, no-evidence/weak-dataset.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.candidate_model_studio.models import (
    CandidateModel,
    DatasetSlice,
    StudioEvidenceBundle,
    ExperimentLineage,
    SupportedExperimentalBoundary,
    CANDIDATE_STATUS_DRAFT,
    CANDIDATE_STATUS_QUARANTINED,
    BOUNDARY_EXPERIMENTAL,
)
from workflow_dataset.candidate_model_studio.store import (
    save_candidate,
    load_candidate,
    list_candidates,
    save_slice,
    load_slice,
    list_slices_for_candidate,
)
from workflow_dataset.candidate_model_studio.dataset_slice import (
    build_slice_from_corrections,
    build_slice_from_council_disagreement,
    build_studio_evidence_bundle,
)
from workflow_dataset.candidate_model_studio.training_paths import (
    get_path_descriptor,
    list_path_ids,
    PATH_PROMPT_CONFIG_ONLY,
    PATH_LIGHTWEIGHT_DISTILLATION,
)
from workflow_dataset.candidate_model_studio.report import (
    build_lineage_summary,
    build_candidate_report,
    get_mission_control_candidate_studio_state,
)
from workflow_dataset.candidate_model_studio.templates import (
    get_template,
    list_templates,
    TEMPLATE_EVALUATOR,
    TEMPLATE_CALMNESS,
)
from workflow_dataset.candidate_model_studio.safety_profiles import (
    get_safety_profile,
    get_production_restrictions,
    list_safety_profiles,
    PROFILE_STRICT_PRODUCTION_ADJACENT,
    PROFILE_EXPERIMENTAL_ONLY,
)


def test_candidate_model_creation(tmp_path):
    """Create and persist a candidate model; load and list."""
    evidence = build_studio_evidence_bundle(
        evidence_ids=["ev_1"],
        correction_ids=["corr_1"],
        cluster_ids=["cluster_abc"],
    )
    lineage = ExperimentLineage(
        candidate_id="",
        evidence_source_type="issue_cluster",
        evidence_source_id="cluster_abc",
        created_at_utc="2025-01-01T00:00:00Z",
        created_by="cli",
    )
    boundary = SupportedExperimentalBoundary(
        candidate_id="",
        boundary=BOUNDARY_EXPERIMENTAL,
        summary="Experimental until promoted",
    )
    c = CandidateModel(
        candidate_id="cand_test001",
        name="Test candidate",
        summary="From cluster_abc",
        status=CANDIDATE_STATUS_DRAFT,
        evidence=evidence,
        dataset_slice_id="slice_001",
        training_path_id=PATH_PROMPT_CONFIG_ONLY,
        lineage=lineage,
        boundary=boundary,
        created_at_utc="2025-01-01T00:00:00Z",
        updated_at_utc="2025-01-01T00:00:00Z",
    )
    c.lineage.candidate_id = c.candidate_id
    c.boundary.candidate_id = c.candidate_id
    path = save_candidate(c, repo_root=tmp_path)
    assert path.exists()
    loaded = load_candidate("cand_test001", repo_root=tmp_path)
    assert loaded is not None
    assert loaded.name == "Test candidate"
    assert loaded.evidence.evidence_count == 3
    candidates = list_candidates(repo_root=tmp_path)
    assert len(candidates) >= 1
    assert any(x.candidate_id == "cand_test001" for x in candidates)


def test_dataset_slice_curation(tmp_path):
    """Build slice from corrections with provenance and exclusion."""
    slice_obj = build_slice_from_corrections(
        candidate_id="cand_1",
        correction_ids=["c1", "c2", "c3"],
        name="Three corrections",
        exclude_ids=["c2"],
        repo_root=tmp_path,
    )
    assert slice_obj.provenance_source == "corrections"
    assert slice_obj.row_count == 2
    assert "c2" in slice_obj.excluded_ids
    assert slice_obj.exclusion_rule_summary
    save_slice(slice_obj, repo_root=tmp_path)
    loaded = load_slice(slice_obj.slice_id, repo_root=tmp_path)
    assert loaded is not None
    assert loaded.row_count == 2


def test_lineage_provenance(tmp_path):
    """Lineage summary reflects source type and id."""
    c = CandidateModel(
        candidate_id="cand_lin",
        name="Lineage test",
        status=CANDIDATE_STATUS_DRAFT,
        evidence=StudioEvidenceBundle(evidence_count=0),
        lineage=ExperimentLineage(
            candidate_id="cand_lin",
            evidence_source_type="adaptation",
            evidence_source_id="adapt_xyz",
            created_by="cli",
        ),
        created_at_utc="2025-01-01T00:00:00Z",
        updated_at_utc="2025-01-01T00:00:00Z",
    )
    save_candidate(c, repo_root=tmp_path)
    summary = build_lineage_summary("cand_lin", repo_root=tmp_path)
    assert summary["found"] is True
    assert summary["evidence_source_type"] == "adaptation"
    assert summary["evidence_source_id"] == "adapt_xyz"


def test_training_path_descriptor():
    """Path descriptors have allowed_scope, risks, required_evaluation_before_promotion."""
    path_ids = list_path_ids()
    assert PATH_PROMPT_CONFIG_ONLY in path_ids
    assert PATH_LIGHTWEIGHT_DISTILLATION in path_ids
    desc = get_path_descriptor(PATH_PROMPT_CONFIG_ONLY)
    assert desc is not None
    assert desc.allowed_scope
    assert len(desc.risks) >= 1
    assert len(desc.required_evaluation_before_promotion) >= 1
    assert get_path_descriptor("nonexistent") is None


def test_quarantined_candidate(tmp_path):
    """Quarantined candidate is listable and reported in mission control state."""
    c = CandidateModel(
        candidate_id="cand_quar",
        name="Quarantined test",
        status=CANDIDATE_STATUS_QUARANTINED,
        evidence=StudioEvidenceBundle(evidence_count=1),
        created_at_utc="2025-01-01T00:00:00Z",
        updated_at_utc="2025-01-01T00:00:00Z",
    )
    save_candidate(c, repo_root=tmp_path)
    listed = list_candidates(repo_root=tmp_path, status=CANDIDATE_STATUS_QUARANTINED)
    assert any(x.candidate_id == "cand_quar" for x in listed)
    state = get_mission_control_candidate_studio_state(repo_root=tmp_path)
    assert state.get("quarantined_count") >= 1
    assert "cand_quar" in state.get("quarantined_ids", [])


def test_no_evidence_weak_dataset(tmp_path):
    """Candidate with empty evidence still has valid report; slice can have row_count 0."""
    slice_obj = build_slice_from_council_disagreement(
        candidate_id="cand_weak",
        review_id="rev_123",
        repo_root=tmp_path,
    )
    assert slice_obj.provenance_source == "council_disagreement"
    assert slice_obj.row_count >= 0
    c = CandidateModel(
        candidate_id="cand_weak",
        name="Weak evidence",
        status=CANDIDATE_STATUS_DRAFT,
        evidence=StudioEvidenceBundle(evidence_count=0, summary="empty"),
        dataset_slice_id=slice_obj.slice_id,
        created_at_utc="2025-01-01T00:00:00Z",
        updated_at_utc="2025-01-01T00:00:00Z",
    )
    save_candidate(c, repo_root=tmp_path)
    report = build_candidate_report("cand_weak", repo_root=tmp_path)
    assert report["found"] is True
    assert report["evidence_count"] == 0


def test_candidate_report_full(tmp_path):
    """Full report includes training_path, lineage, boundary."""
    c = CandidateModel(
        candidate_id="cand_report",
        name="Report test",
        summary="For report",
        status=CANDIDATE_STATUS_DRAFT,
        evidence=StudioEvidenceBundle(evidence_ids=["ev_1"], evidence_count=1),
        dataset_slice_id="slice_r",
        training_path_id=PATH_PROMPT_CONFIG_ONLY,
        created_at_utc="2025-01-01T00:00:00Z",
        updated_at_utc="2025-01-01T00:00:00Z",
    )
    save_candidate(c, repo_root=tmp_path)
    report = build_candidate_report("cand_report", repo_root=tmp_path)
    assert report["found"] is True
    assert report["training_path"] is not None
    assert "required_evaluation_before_promotion" in (report["training_path"] or {})


# ----- M42H.1: Candidate templates + distillation safety profiles -----


def test_candidate_template_evaluator():
    """Evaluator template has critique_evaluator path and strict_production_adjacent safety."""
    t = get_template(TEMPLATE_EVALUATOR)
    assert t is not None
    assert t.template_id == TEMPLATE_EVALUATOR
    assert t.default_training_path_id == "critique_evaluator"
    assert t.default_safety_profile_id == PROFILE_STRICT_PRODUCTION_ADJACENT
    assert "council_disagreement" in t.suggested_provenance_sources


def test_candidate_template_calmness():
    """Calmness template has prompt_config_only path and experimental_only safety."""
    t = get_template(TEMPLATE_CALMNESS)
    assert t is not None
    assert t.default_training_path_id == "prompt_config_only"
    assert t.default_safety_profile_id == PROFILE_EXPERIMENTAL_ONLY


def test_list_templates():
    """List templates returns evaluator, vertical_specialist, routing, calmness."""
    templates = list_templates()
    ids = [t.template_id for t in templates]
    assert TEMPLATE_EVALUATOR in ids
    assert "vertical_specialist" in ids
    assert "routing" in ids
    assert TEMPLATE_CALMNESS in ids


def test_safety_profile_strict_production_adjacent():
    """Strict production-adjacent profile has require_council and no_weight_changes."""
    p = get_safety_profile(PROFILE_STRICT_PRODUCTION_ADJACENT)
    assert p is not None
    assert p.production_restrictions.require_council_before_supported is True
    assert p.production_restrictions.no_weight_changes_in_production_scope is True


def test_safety_profile_production_restrictions():
    """get_production_restrictions returns restrictions for a profile."""
    r = get_production_restrictions(PROFILE_EXPERIMENTAL_ONLY)
    assert r is not None
    assert r.experimental_only_until_council is True
    assert r.max_slice_size == 5000


def test_list_safety_profiles():
    """List safety profiles includes strict_production_adjacent, experimental_only, council_gated, lab_research."""
    profiles = list_safety_profiles()
    ids = [p.profile_id for p in profiles]
    assert PROFILE_STRICT_PRODUCTION_ADJACENT in ids
    assert PROFILE_EXPERIMENTAL_ONLY in ids
    assert "council_gated" in ids
    assert "lab_research" in ids


def test_training_path_has_production_restrictions_summary():
    """Training path descriptor has default_safety_profile_id and production_restrictions_summary."""
    desc = get_path_descriptor(PATH_PROMPT_CONFIG_ONLY)
    assert desc is not None
    assert desc.default_safety_profile_id == "strict_production_adjacent"
    assert "Council" in desc.production_restrictions_summary or "production" in desc.production_restrictions_summary.lower()


def test_create_with_template_sets_template_and_safety(tmp_path):
    """Create from corrections with template_id sets template_id and safety_profile_id on candidate."""
    from workflow_dataset.candidate_model_studio.create import create_candidate_from_corrections
    c = create_candidate_from_corrections(
        correction_ids=["c1", "c2"],
        name="With template",
        template_id=TEMPLATE_EVALUATOR,
        repo_root=tmp_path,
    )
    assert c.template_id == TEMPLATE_EVALUATOR
    assert c.safety_profile_id == PROFILE_STRICT_PRODUCTION_ADJACENT
    assert c.training_path_id == "critique_evaluator"

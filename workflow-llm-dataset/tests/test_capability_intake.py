"""M21: Tests for capability intake — models, registry, role, risk, fit, report, pack manifest."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from workflow_dataset.capability_intake.source_models import (
    ExternalSourceCandidate,
    SourceRole,
    SourceAdoptionDecision,
)
from workflow_dataset.capability_intake.source_registry import (
    load_source_registry,
    save_source_registry,
    list_sources,
    get_source,
)
from workflow_dataset.capability_intake.repo_classifier import classify_role
from workflow_dataset.capability_intake.source_risk import assess_risk
from workflow_dataset.capability_intake.source_fit import assess_fit
from workflow_dataset.capability_intake.source_intake import intake_candidate
from workflow_dataset.capability_intake.source_report import write_source_report
from workflow_dataset.capability_intake.repo_parser import parse_manifest_file, manifest_to_candidate, parse_local_manifest
from workflow_dataset.capability_intake.manifest_builder import candidate_to_manifest, build_manifest_template
from workflow_dataset.capability_intake.search_index import build_search_index, load_search_index, search_by_role, search_by_adoption
from workflow_dataset.capability_intake.pack_models import PackManifest, validate_pack_manifest
from workflow_dataset.capability_intake.repo_ranker import RepoTaskFitQuery, RepoTaskFitResult, rank_sources_for_query


def test_external_source_candidate_model() -> None:
    c = ExternalSourceCandidate(
        source_id="test",
        name="Test Repo",
        source_type="repo",
        recommended_role=SourceRole.PARSER.value,
        adoption_recommendation=SourceAdoptionDecision.REFERENCE_ONLY.value,
    )
    assert c.source_id == "test"
    assert c.recommended_role == "parser"


def test_registry_load_save(tmp_path: Path) -> None:
    reg = tmp_path / "registry.json"
    entries = [
        {"source_id": "a", "name": "A", "adoption_recommendation": "reference_only"},
        {"source_id": "b", "name": "B", "adoption_recommendation": "reject"},
    ]
    save_source_registry(entries, reg)
    loaded = load_source_registry(reg)
    assert len(loaded) == 2
    assert loaded[0]["source_id"] == "a"


def test_list_sources_filter(tmp_path: Path) -> None:
    save_source_registry([
        {"source_id": "u1", "name": "U1", "unresolved_reason": "no url"},
        {"source_id": "r1", "name": "R1", "adoption_recommendation": "reject"},
    ], tmp_path / "r.json")
    unresolved = list_sources(tmp_path / "r.json", unresolved_only=True)
    assert len(unresolved) == 1
    assert unresolved[0].source_id == "u1"
    rejected = list_sources(tmp_path / "r.json", adoption_filter="reject")
    assert len(rejected) == 1
    assert rejected[0].source_id == "r1"


def test_get_source(tmp_path: Path) -> None:
    save_source_registry([{"source_id": "x", "name": "X"}], tmp_path / "r.json")
    s = get_source("x", tmp_path / "r.json")
    assert s is not None
    assert s.name == "X"
    assert get_source("nonexistent", tmp_path / "r.json") is None


def test_classify_role() -> None:
    c = ExternalSourceCandidate(description="multi-agent orchestration routing")
    assert classify_role(c) == SourceRole.AGENT_ORCHESTRATOR.value
    c2 = ExternalSourceCandidate(description="parser for documents")
    assert classify_role(c2) == SourceRole.PARSER.value


def test_assess_risk() -> None:
    c = ExternalSourceCandidate(description="MIT license", license="MIT")
    assert assess_risk(c) == "low"
    c2 = ExternalSourceCandidate(description="unsafe network", notes="reject")
    assert assess_risk(c2) == "high"


def test_assess_fit() -> None:
    c = ExternalSourceCandidate(description="local offline agent")
    local, cloud = assess_fit(c)
    assert local in ("high", "medium", "low")
    assert cloud in ("high", "medium", "low", "none")


def test_intake_candidate() -> None:
    raw = {"source_id": "t", "name": "T", "description": "local parser"}
    c = intake_candidate(raw)
    assert c.source_id == "t"
    assert c.recommended_role
    assert c.safety_risk_level
    assert c.adoption_recommendation


def test_write_source_report(tmp_path: Path) -> None:
    save_source_registry([{"source_id": "s1", "name": "S1", "adoption_recommendation": "reference_only"}], tmp_path / "r.json")
    out = write_source_report(output_path=tmp_path / "report.md", registry_path=tmp_path / "r.json")
    assert out.exists()
    assert "Capability intake" in out.read_text()
    assert "s1" in out.read_text()


def test_parse_manifest_file(tmp_path: Path) -> None:
    m = tmp_path / "m.json"
    m.write_text('{"name": "P", "description": "A parser"}')
    raw = parse_manifest_file(m)
    assert raw["name"] == "P"
    assert parse_manifest_file(tmp_path / "nonexistent.json") == {}


def test_manifest_to_candidate() -> None:
    raw = {"name": "Test", "description": "local agent runtime"}
    c = manifest_to_candidate(raw, "tid")
    assert c.source_id == "tid"
    assert c.recommended_role
    assert c.adoption_recommendation


def test_parse_local_manifest(tmp_path: Path) -> None:
    (tmp_path / "m.json").write_text('{"name": "X", "description": "Something"}')
    c = parse_local_manifest(tmp_path / "m.json")
    assert c is not None
    assert c.name == "X"
    assert parse_local_manifest(tmp_path / "missing.json") is None


def test_candidate_to_manifest() -> None:
    c = ExternalSourceCandidate(source_id="c1", name="C1", recommended_role="parser")
    m = candidate_to_manifest(c)
    assert m["source_id"] == "c1"
    assert m["recommended_role"] == "parser"


def test_build_manifest_template() -> None:
    t = build_manifest_template()
    assert "source_id" in t
    assert "name" in t


def test_search_index(tmp_path: Path) -> None:
    save_source_registry([{"source_id": "i1", "name": "I1", "recommended_role": "parser", "adoption_recommendation": "reference_only"}], tmp_path / "r.json")
    idx_path = build_search_index(registry_path=tmp_path / "r.json", index_path=tmp_path / "idx.json")
    assert idx_path.exists()
    entries = load_search_index(idx_path)
    assert len(entries) == 1
    assert search_by_role("parser", idx_path) == entries
    assert search_by_adoption("reference_only", idx_path) == entries


def test_pack_manifest_validation() -> None:
    valid, errs = validate_pack_manifest({})
    assert not valid
    assert "pack_id" in str(errs)
    valid, errs = validate_pack_manifest({"pack_id": "p1", "name": "P", "version": "0.1.0"})
    assert valid
    valid, errs = validate_pack_manifest({"pack_id": "p2", "name": "P2", "version": "0.1.0", "safety_policies": {"sandbox_only": False}})
    assert not valid
    assert "sandbox_only" in str(errs)


def test_sources_list_cli(tmp_path: Path) -> None:
    from typer.testing import CliRunner
    from workflow_dataset.cli import app
    save_source_registry([{"source_id": "cli1", "name": "CLI1", "adoption_recommendation": "reference_only"}], tmp_path / "r.json")
    runner = CliRunner()
    result = runner.invoke(app, ["sources", "list", "--registry", str(tmp_path / "r.json")])
    assert result.exit_code == 0
    assert "cli1" in result.output


def test_sources_show_cli(tmp_path: Path) -> None:
    from typer.testing import CliRunner
    from workflow_dataset.cli import app
    save_source_registry([{"source_id": "show1", "name": "Show One", "adoption_recommendation": "reference_only"}], tmp_path / "r.json")
    runner = CliRunner()
    result = runner.invoke(app, ["sources", "show", "show1", "--registry", str(tmp_path / "r.json")])
    assert result.exit_code == 0
    assert "Show One" in result.output


def test_sources_report_cli(tmp_path: Path) -> None:
    from typer.testing import CliRunner
    from workflow_dataset.cli import app
    save_source_registry([{"source_id": "rpt", "name": "Rpt", "adoption_recommendation": "reference_only"}], tmp_path / "r.json")
    runner = CliRunner()
    out = tmp_path / "report.md"
    result = runner.invoke(app, ["sources", "report", "--registry", str(tmp_path / "r.json"), "--output", str(out)])
    assert result.exit_code == 0
    assert out.exists()


def test_repo_ranker_query_result() -> None:
    q = RepoTaskFitQuery(role="ops", workflow_type="reporting", orchestration_need=True)
    assert q.role == "ops"
    assert q.orchestration_need is True
    r = RepoTaskFitResult(source_id="x", fit_score=0.5, adoption_recommendation="reference_only")
    assert r.fit_score == 0.5


def test_rank_sources_for_query(tmp_path: Path) -> None:
    save_source_registry([
        {"source_id": "orch", "name": "Orch", "recommended_role": "agent_orchestrator", "safety_risk_level": "low", "adoption_recommendation": "reference_only", "local_runtime_fit": "high", "product_layers": ["agent_runtime"]},
        {"source_id": "ui", "name": "UI", "recommended_role": "dashboard_ui", "safety_risk_level": "medium", "adoption_recommendation": "reference_only", "local_runtime_fit": "medium"},
    ], tmp_path / "r.json")
    query = RepoTaskFitQuery(role="ops", orchestration_need=True)
    results = rank_sources_for_query(query, registry_path=tmp_path / "r.json", top_k=5)
    assert len(results) <= 2
    assert all(isinstance(r, RepoTaskFitResult) for r in results)
    assert all(0 <= r.fit_score <= 1 for r in results)


def test_packs_validate_manifest_cli(tmp_path: Path) -> None:
    from typer.testing import CliRunner
    from workflow_dataset.cli import app
    good = tmp_path / "good.json"
    good.write_text('{"pack_id": "p1", "name": "P1", "version": "0.1.0"}')
    runner = CliRunner()
    result = runner.invoke(app, ["packs", "validate-manifest", str(good)])
    assert result.exit_code == 0
    bad = tmp_path / "bad.json"
    bad.write_text('{"pack_id": "p2", "name": "P2", "version": "0.1.0", "safety_policies": {"sandbox_only": false}}')
    result2 = runner.invoke(app, ["packs", "validate-manifest", str(bad)])
    assert result2.exit_code == 1


def test_sources_rank_cli(tmp_path: Path) -> None:
    from typer.testing import CliRunner
    from workflow_dataset.cli import app
    save_source_registry([{"source_id": "s1", "name": "S1", "recommended_role": "agent_orchestrator", "adoption_recommendation": "reference_only", "safety_risk_level": "low"}], tmp_path / "r.json")
    runner = CliRunner()
    result = runner.invoke(app, ["sources", "rank", "--role", "ops", "--registry", str(tmp_path / "r.json"), "--top", "5"])
    assert result.exit_code == 0
    assert "s1" in result.output or "fit=" in result.output


def test_packs_list_cli(tmp_path: Path) -> None:
    from typer.testing import CliRunner
    from workflow_dataset.cli import app
    (tmp_path / "packs").mkdir(parents=True)
    (tmp_path / "packs" / "ops.json").write_text('{"pack_id":"ops","name":"Ops pack","version":"0.1.0"}')
    runner = CliRunner()
    result = runner.invoke(app, ["packs", "list", "--packs-dir", str(tmp_path / "packs")])
    assert result.exit_code == 0
    assert "ops" in result.output

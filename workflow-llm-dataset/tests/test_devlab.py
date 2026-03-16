"""
M21W: Tests for devlab — repo intake, model lab, dev loop.
No network required for unit tests; clone tests optional/skipped if no git.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


def test_devlab_config_paths(tmp_path: Path) -> None:
    """Devlab paths are under sandbox root."""
    from workflow_dataset.devlab.config import (
        get_devlab_root,
        get_repos_dir,
        get_reports_dir,
        get_registry_path,
    )
    root = get_devlab_root(tmp_path)
    assert root == tmp_path
    assert get_repos_dir(tmp_path).name == "repos"
    assert get_reports_dir(tmp_path).name == "reports"
    assert get_registry_path(tmp_path).name == "registry.json"


def test_repo_id_from_url() -> None:
    """Repo id derived from GitHub URL."""
    from workflow_dataset.devlab.repo_intake import _repo_id_from_url
    assert _repo_id_from_url("https://github.com/owner/repo") == "owner_repo"
    assert _repo_id_from_url("https://github.com/owner/repo.git") == "owner_repo"
    assert _repo_id_from_url("git@github.com:owner/repo.git") == "owner_repo"


def test_register_and_list(tmp_path: Path) -> None:
    """Register repo and list registry."""
    from workflow_dataset.devlab.repo_intake import register_repo, load_registry
    register_repo("https://github.com/foo/bar", label="test", category="retrieval", root=tmp_path)
    entries = load_registry(tmp_path)
    assert len(entries) == 1
    assert entries[0]["repo_id"] == "foo_bar"
    assert entries[0]["url"] == "https://github.com/foo/bar"
    assert entries[0]["category"] == "retrieval"


def test_parse_only_no_execution(tmp_path: Path) -> None:
    """Parse-only reads files; does not execute."""
    from workflow_dataset.devlab.repo_intake import parse_only
    (tmp_path / "README.md").write_text("# Hi\n", encoding="utf-8")
    (tmp_path / "requirements.txt").write_text("requests\n", encoding="utf-8")
    out = parse_only(tmp_path)
    assert "readme_preview" in out
    assert "Hi" in out.get("readme_preview", "")
    assert "deps" in out
    assert "requirements.txt" in out.get("deps", {})
    assert "file_tree" in out


def test_ingest_repo_requires_registry(tmp_path: Path) -> None:
    """Ingest with unknown repo_id raises."""
    from workflow_dataset.devlab.repo_intake import ingest_repo
    with pytest.raises(ValueError, match="not in registry"):
        ingest_repo("unknown_repo_xyz", root=tmp_path)


def test_write_intake_report(tmp_path: Path) -> None:
    """write_intake_report produces JSON report with D2 scores and recommendation (no clone when dir exists)."""
    from workflow_dataset.devlab.repo_intake import (
        register_repo,
        get_repos_dir,
        write_intake_report,
    )
    register_repo("https://github.com/foo/bar", label="test", category="evaluation", root=tmp_path)
    repo_dir = get_repos_dir(tmp_path) / "foo_bar"
    repo_dir.mkdir(parents=True, exist_ok=True)
    (repo_dir / "README.md").write_text("# Bar\nA test repo. Eval harness and workflow.", encoding="utf-8")
    (repo_dir / "requirements.txt").write_text("requests\n", encoding="utf-8")
    path = write_intake_report("foo_bar", root=tmp_path)
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["repo_id"] == "foo_bar"
    assert "summary" in data
    assert "parse" in data
    assert data["parse"]["file_tree_count"] >= 2
    assert "requirements.txt" in data["parse"]["deps_files"]
    assert "usefulness_scores" in data
    assert "license_triage" in data
    assert data["d2_recommendation"] in ("inspect_further", "borrow_pattern_only", "prototype_candidate", "do_not_use")
    assert "relevance" in data.get("usefulness_scores", {})
    assert "license_visible" in data.get("license_triage", {})


def test_model_lab_unknown_provider() -> None:
    """Unknown provider returns message, no silent fallback."""
    from workflow_dataset.devlab.model_lab import complete
    out = complete("unknown_provider", "Hello")
    assert "Unknown provider" in out or "unknown" in out.lower()


def test_model_lab_compare_returns_list() -> None:
    """compare_models returns list of result dicts."""
    from workflow_dataset.devlab.model_lab import compare_models
    results = compare_models("weekly_status", ["ollama"], root=Path("/tmp/devlab_test_nonexist"))
    assert isinstance(results, list)
    assert len(results) == 1
    assert results[0]["provider"] == "ollama"
    assert "output" in results[0]


def test_write_compare_report(tmp_path: Path) -> None:
    """write_compare_report writes JSON under sandbox."""
    from workflow_dataset.devlab.model_lab import write_compare_report
    results = [{"provider": "ollama", "model": "x", "output": "y", "notes": ""}]
    path = write_compare_report("weekly_status", results, root=tmp_path)
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["workflow"] == "weekly_status"
    assert len(data["results"]) == 1


def test_loop_status_empty(tmp_path: Path) -> None:
    """loop_status returns empty when no run."""
    from workflow_dataset.devlab.dev_loop import loop_status
    s = loop_status(root=tmp_path)
    assert s == {} or "running" in s or "last_run" in s


def test_stop_loop_clears_flag(tmp_path: Path) -> None:
    """stop_loop sets running false."""
    from workflow_dataset.devlab.dev_loop import _write_loop_status, _read_loop_status, stop_loop
    _write_loop_status({"running": True}, tmp_path)
    stop_loop(tmp_path)
    s = _read_loop_status(tmp_path)
    assert s.get("running") is False


def test_d2_repo_scoring() -> None:
    """D2 usefulness scoring returns relevance, clarity, patterns, complexity, risk."""
    from workflow_dataset.devlab.repo_scoring import score_repo_usefulness, usefulness_composite
    parsed = {
        "readme_preview": "# Eval harness. Workflow and API. Module for benchmarking.",
        "license_note": "MIT License",
        "deps": {"requirements.txt": "requests"},
        "file_tree": [{"path": "src", "dir": True}, {"path": "README.md", "dir": False}],
    }
    scores = score_repo_usefulness(parsed, {"category": "evaluation"})
    assert "relevance" in scores
    assert "code_doc_clarity" in scores
    assert "reusable_patterns" in scores
    assert "implementation_complexity" in scores
    assert "risk" in scores
    comp = usefulness_composite(scores)
    assert 0 <= comp <= 1


def test_d2_license_triage() -> None:
    """D2 license triage returns license_visible, dependency_heaviness, use_as."""
    from workflow_dataset.devlab.license_triage import triage_license_risk
    parsed = {"license_note": "MIT License", "deps": {}, "readme_preview": ""}
    triage = triage_license_risk(parsed)
    assert "license_visible" in triage
    assert triage["dependency_heaviness"] in ("light", "medium", "heavy")
    assert triage["use_as"] in ("inspiration", "direct_reuse", "unclear")


def test_d2_recommend_d2() -> None:
    """D2 recommendation is one of inspect_further, borrow_pattern_only, prototype_candidate, do_not_use."""
    from workflow_dataset.devlab.repo_scoring import recommend_d2, D2_RECOMMENDATIONS
    scores = {"relevance": 0.5, "risk": 0.1, "reusable_patterns": 0.4}
    triage = {"legal_operational_risk": "low", "use_as": "direct_reuse"}
    rec = recommend_d2(scores, triage)
    assert rec in D2_RECOMMENDATIONS


def test_d2_shortlist_empty(tmp_path: Path) -> None:
    """Shortlist with no scored reports returns empty categories."""
    from workflow_dataset.devlab.shortlist import build_shortlist
    from workflow_dataset.devlab.config import get_reports_dir
    reports_dir = get_reports_dir(tmp_path)
    shortlist = build_shortlist(reports_dir, [])
    for cat, entries in shortlist.items():
        assert entries == []


def test_d2_shortlist_from_reports(tmp_path: Path) -> None:
    """Shortlist ranks scored reports by category and composite score."""
    from workflow_dataset.devlab.shortlist import build_shortlist
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir(parents=True)
    (reports_dir / "repo_intake_report_foo.json").write_text(json.dumps({
        "repo_id": "foo",
        "url": "https://github.com/a/foo",
        "usefulness_scores": {"relevance": 0.8, "code_doc_clarity": 0.5, "reusable_patterns": 0.4, "implementation_complexity": 0.3, "risk": 0.1},
        "d2_recommendation": "prototype_candidate",
        "license_triage": {"use_as": "direct_reuse"},
    }), encoding="utf-8")
    registry = [{"repo_id": "foo", "category": "UI", "url": "https://github.com/a/foo"}]
    shortlist = build_shortlist(reports_dir, registry)
    assert "UI" in shortlist
    assert len(shortlist["UI"]) == 1
    assert shortlist["UI"][0]["repo_id"] == "foo"
    assert shortlist["UI"][0]["composite_score"] >= 0


def test_d2_score_all_reports(tmp_path: Path) -> None:
    """score_all_reports updates reports with D2 scores when repo dir exists."""
    from workflow_dataset.devlab.repo_intake import (
        register_repo,
        get_repos_dir,
        get_reports_dir,
        write_intake_report,
        score_all_reports,
    )
    register_repo("https://github.com/f/b", label="x", category="eval", root=tmp_path)
    repo_dir = get_repos_dir(tmp_path) / "f_b"
    repo_dir.mkdir(parents=True)
    (repo_dir / "README.md").write_text("# Eval\n", encoding="utf-8")
    write_intake_report("f_b", root=tmp_path)
    updated = score_all_reports(tmp_path)
    assert len(updated) >= 1
    assert updated[0]["d2_recommendation"] in ("inspect_further", "borrow_pattern_only", "prototype_candidate", "do_not_use")


def test_run_loop_produces_artifacts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """run_loop writes devlab_report.md and next_patch_plan.md."""
    import subprocess
    from workflow_dataset.devlab.dev_loop import run_loop

    def fake_run(*args: object, **kwargs: object) -> object:
        from types import SimpleNamespace
        return SimpleNamespace(returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    status = run_loop(workflow="weekly_status", providers=[], root=tmp_path)
    assert status.get("devlab_report")
    assert Path(status["devlab_report"]).exists()
    assert status.get("next_patch_plan")
    assert "running" in status
    assert status.get("running") is False


# ----- D3: Proposal generator from repo intake + model compare -----


def test_proposal_generator_load_intake_reports_empty(tmp_path: Path) -> None:
    """load_intake_reports returns empty list when no reports."""
    from workflow_dataset.devlab.proposal_generator import load_intake_reports
    reports = load_intake_reports(tmp_path)
    assert reports == []


def test_proposal_generator_load_intake_reports_one(tmp_path: Path) -> None:
    """load_intake_reports returns report dicts with repo_id and _path."""
    from workflow_dataset.devlab.proposal_generator import load_intake_reports
    from workflow_dataset.devlab.config import get_reports_dir
    reports_dir = get_reports_dir(tmp_path)
    reports_dir.mkdir(parents=True, exist_ok=True)
    (reports_dir / "repo_intake_report_foo.json").write_text(
        json.dumps({"repo_id": "foo", "summary": "Test repo", "d2_recommendation": "inspect_further"}),
        encoding="utf-8",
    )
    reports = load_intake_reports(tmp_path)
    assert len(reports) == 1
    assert reports[0]["repo_id"] == "foo"
    assert "_path" in reports[0]


def test_proposal_generator_load_model_compare_missing(tmp_path: Path) -> None:
    """load_model_compare_report returns None when file absent."""
    from workflow_dataset.devlab.proposal_generator import load_model_compare_report
    assert load_model_compare_report(tmp_path) is None


def test_proposal_generator_load_model_compare_present(tmp_path: Path) -> None:
    """load_model_compare_report returns dict when model_compare_report.json exists."""
    from workflow_dataset.devlab.proposal_generator import load_model_compare_report
    from workflow_dataset.devlab.config import get_model_compare_dir
    compare_dir = get_model_compare_dir(tmp_path)
    compare_dir.mkdir(parents=True, exist_ok=True)
    (compare_dir / "model_compare_report.json").write_text(
        json.dumps({"workflow": "weekly_status", "results": [{"provider": "ollama", "model": "x", "output": "y"}]}),
        encoding="utf-8",
    )
    mc = load_model_compare_report(tmp_path)
    assert mc is not None
    assert mc["workflow"] == "weekly_status"
    assert len(mc["results"]) == 1


def test_generate_proposal_empty(tmp_path: Path) -> None:
    """D3: generate_proposal with no intake and no model compare still writes all three artifacts + manifest."""
    from workflow_dataset.devlab.proposal_generator import generate_proposal
    from workflow_dataset.devlab.config import get_proposals_dir
    result = generate_proposal(tmp_path)
    assert result["proposal_id"]
    assert result["intake_count"] == 0
    assert result["model_compare_present"] is False
    prop_dir = Path(result["proposal_path"])
    assert (prop_dir / "devlab_proposal.md").exists()
    assert (prop_dir / "cursor_prompt.txt").exists()
    assert (prop_dir / "rfc_skeleton.md").exists()
    assert (prop_dir / "manifest.json").exists()
    md = (prop_dir / "devlab_proposal.md").read_text(encoding="utf-8")
    assert "advisory" in md.lower()
    assert "No repo intake reports" in md or "No model comparison" in md
    manifest = json.loads((prop_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["source"] == "proposal_generator"
    assert manifest["status"] == "pending"


def test_generate_proposal_with_intake_and_model_compare(tmp_path: Path) -> None:
    """D3: generate_proposal includes intake summary and model compare in devlab_proposal.md."""
    from workflow_dataset.devlab.proposal_generator import generate_proposal
    from workflow_dataset.devlab.config import get_reports_dir, get_model_compare_dir
    get_reports_dir(tmp_path).mkdir(parents=True, exist_ok=True)
    (get_reports_dir(tmp_path) / "repo_intake_report_foo.json").write_text(
        json.dumps({
            "repo_id": "foo",
            "summary": "Eval harness repo.",
            "d2_recommendation": "prototype_candidate",
            "composite_score": 0.6,
            "reuse_or_inspiration": "inspiration",
        }),
        encoding="utf-8",
    )
    get_model_compare_dir(tmp_path).mkdir(parents=True, exist_ok=True)
    (get_model_compare_dir(tmp_path) / "model_compare_report.json").write_text(
        json.dumps({
            "workflow": "weekly_status",
            "results": [{"provider": "ollama", "model": "llama3.2", "output": "Done."}],
        }),
        encoding="utf-8",
    )
    result = generate_proposal(tmp_path)
    assert result["intake_count"] == 1
    assert result["model_compare_present"] is True
    md = Path(result["devlab_proposal_md"]).read_text(encoding="utf-8")
    assert "foo" in md
    assert "weekly_status" in md
    assert "ollama" in md
    cursor = Path(result["cursor_prompt_txt"]).read_text(encoding="utf-8")
    assert "repo intake" in cursor.lower()
    assert "model comparison" in cursor.lower()


def test_get_proposal_includes_devlab_proposal_md(tmp_path: Path) -> None:
    """get_proposal returns devlab_proposal_md path when present (D3 artifact)."""
    from workflow_dataset.devlab.proposal_generator import generate_proposal
    from workflow_dataset.devlab.proposals import get_proposal
    result = generate_proposal(tmp_path)
    proposal_id = result["proposal_id"]
    p = get_proposal(proposal_id, tmp_path)
    assert p is not None
    assert p.get("devlab_proposal_md")
    assert Path(p["devlab_proposal_md"]).exists()

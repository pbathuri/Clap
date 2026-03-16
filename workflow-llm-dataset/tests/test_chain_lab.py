"""
M23A: Tests for internal chain lab — definition, manifest, runner, report, compare.
All local sandbox; no network, no auto-apply.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from workflow_dataset.chain_lab.config import get_chain_lab_root, get_chains_dir, get_runs_dir
from workflow_dataset.chain_lab.definition import (
    load_chain,
    save_chain,
    list_chains,
    validate_chain,
)
from workflow_dataset.chain_lab.manifest import (
    run_dir_for,
    step_result_dir,
    load_run_manifest,
    save_run_manifest,
    list_run_ids,
    get_latest_run_id,
)
from workflow_dataset.chain_lab.eval_bridge import list_chain_runs_for_eval, get_chain_run_for_eval
from workflow_dataset.chain_lab.report import (
    chain_run_report,
    chain_artifact_tree,
    resolve_run_id,
    failure_report_section,
)
from workflow_dataset.chain_lab.compare import compare_chain_runs
from workflow_dataset.chain_lab.definition import get_step_by_id_or_index
from workflow_dataset.chain_lab.runner import resume_chain, retry_step


def test_chain_lab_paths(tmp_path: Path) -> None:
    root = get_chain_lab_root(tmp_path)
    assert root.is_dir()
    chains_dir = get_chains_dir(tmp_path)
    runs_dir = get_runs_dir(tmp_path)
    assert chains_dir.is_dir()
    assert runs_dir.is_dir()
    assert chains_dir.samefile(root / "chains")
    assert runs_dir.samefile(root / "runs")


def test_validate_chain_rejects_empty_id() -> None:
    with pytest.raises(ValueError, match="non-empty id"):
        validate_chain({"id": "", "steps": [{"id": "s1", "type": "cli"}]})


def test_validate_chain_rejects_empty_steps() -> None:
    with pytest.raises(ValueError, match="non-empty steps"):
        validate_chain({"id": "c1", "steps": []})


def test_save_and_load_chain(tmp_path: Path) -> None:
    definition = {
        "id": "demo_chain",
        "description": "One demo step",
        "steps": [
            {"id": "step1", "type": "cli", "label": "Demo", "params": {"args": ["release", "verify"]}},
        ],
        "variant_label": "v1",
    }
    validate_chain(definition)
    path = save_chain(definition, repo_root=tmp_path)
    assert path.exists()
    loaded = load_chain("demo_chain", repo_root=tmp_path)
    assert loaded["id"] == "demo_chain"
    assert len(loaded["steps"]) == 1
    assert loaded["steps"][0]["params"].get("args") == ["release", "verify"]
    assert loaded["variant_label"] == "v1"


def test_list_chains(tmp_path: Path) -> None:
    save_chain({"id": "a", "steps": [{"id": "s1"}]}, repo_root=tmp_path)
    save_chain({"id": "b", "description": "B desc", "steps": [{"id": "s1"}, {"id": "s2"}]}, repo_root=tmp_path)
    chains = list_chains(repo_root=tmp_path)
    assert len(chains) == 2
    ids = [c["id"] for c in chains]
    assert "a" in ids and "b" in ids
    b = next(c for c in chains if c["id"] == "b")
    assert b["step_count"] == 2
    assert "B desc" in (b.get("description") or "")


def test_run_manifest_save_load(tmp_path: Path) -> None:
    run_id = "test_run_001"
    run_dir_for(run_id, tmp_path)
    step_dir = step_result_dir(run_id, 0, tmp_path)
    assert step_dir.is_dir()

    save_run_manifest(
        run_id=run_id,
        chain_id="demo_chain",
        variant_label="v1",
        status="success",
        step_results=[
            {"step_index": 0, "step_id": "s1", "status": "success", "output_paths": []},
        ],
        started_at="2025-01-01T00:00:00Z",
        ended_at="2025-01-01T00:01:00Z",
        repo_root=tmp_path,
    )
    manifest = load_run_manifest(run_id, tmp_path)
    assert manifest is not None
    assert manifest["run_id"] == run_id
    assert manifest["chain_id"] == "demo_chain"
    assert manifest["status"] == "success"
    assert len(manifest["step_results"]) == 1
    assert manifest["step_results"][0]["step_id"] == "s1"


def test_list_run_ids(tmp_path: Path) -> None:
    for rid in ["r1", "r2"]:
        save_run_manifest(
            run_id=rid, chain_id="c", variant_label="", status="success",
            step_results=[], started_at="2025-01-01T00:00:00Z", repo_root=tmp_path,
        )
    ids = list_run_ids(repo_root=tmp_path, limit=10)
    assert len(ids) == 2
    assert "r1" in ids and "r2" in ids


def test_chain_run_report(tmp_path: Path) -> None:
    run_id = "report_run"
    save_run_manifest(
        run_id=run_id,
        chain_id="demo",
        variant_label="v1",
        status="failed",
        step_results=[
            {"step_index": 0, "step_id": "s1", "status": "success", "started_at": "2025-01-01T00:00:00Z", "ended_at": "2025-01-01T00:00:01Z", "output_paths": []},
            {"step_index": 1, "step_id": "s2", "status": "failed", "error": "exit code 1", "started_at": "2025-01-01T00:00:01Z", "ended_at": "2025-01-01T00:00:02Z", "output_paths": []},
        ],
        started_at="2025-01-01T00:00:00Z",
        ended_at="2025-01-01T00:00:02Z",
        failure_summary="Step 1 failed",
        repo_root=tmp_path,
    )
    report = chain_run_report(run_id, repo_root=tmp_path)
    assert "Chain run report" in report
    assert run_id in report
    assert "demo" in report
    assert "failed" in report
    assert "Failure summary" in report
    assert "Step 0" in report and "Step 1" in report


def test_chain_artifact_tree(tmp_path: Path) -> None:
    run_id = "tree_run"
    save_run_manifest(
        run_id=run_id,
        chain_id="c",
        variant_label="",
        status="success",
        step_results=[{"step_index": 0, "step_id": "s1", "status": "success", "output_paths": ["/tmp/out.txt"]}],
        started_at="2025-01-01T00:00:00Z",
        ended_at="2025-01-01T00:00:01Z",
        repo_root=tmp_path,
    )
    tree = chain_artifact_tree(run_id, repo_root=tmp_path)
    assert tree["run_id"] == run_id
    assert tree["chain_id"] == "c"
    assert len(tree["steps"]) == 1
    assert tree["steps"][0]["output_paths"] == ["/tmp/out.txt"]


def test_compare_chain_runs(tmp_path: Path) -> None:
    for rid, status in [("ca", "success"), ("cb", "failed")]:
        save_run_manifest(
            run_id=rid, chain_id="c", variant_label="",
            status=status, step_results=[
                {"step_index": 0, "step_id": "s1", "status": "success" if rid == "ca" else "failed", "error": None if rid == "ca" else "exit 1"},
            ],
            started_at="2025-01-01T00:00:00Z", ended_at="2025-01-01T00:00:01Z",
            failure_summary=None if rid == "ca" else "Step 0 failed",
            repo_root=tmp_path,
        )
    diff = compare_chain_runs("ca", "cb", repo_root=tmp_path)
    assert diff["run_id_a"] == "ca" and diff["run_id_b"] == "cb"
    assert diff["run_a"]["status"] == "success"
    assert diff["run_b"]["status"] == "failed"
    assert diff["status_diff"] == {"a": "success", "b": "failed"}
    assert len(diff["step_status_diff"]) >= 1
    assert diff["failure_diff"] is not None


def test_compare_missing_runs(tmp_path: Path) -> None:
    diff = compare_chain_runs("missing_a", "missing_b", repo_root=tmp_path)
    assert diff["run_a"] == "not_found" and diff["run_b"] == "not_found"


def test_chain_list_cli(tmp_path: Path) -> None:
    """CLI: chain list shows definitions (or empty message). Skipped if CLI deps (e.g. yaml) missing."""
    pytest.importorskip("yaml")
    from typer.testing import CliRunner
    from workflow_dataset.cli import app
    runner = CliRunner()
    result = runner.invoke(app, ["chain", "list", "--repo-root", str(tmp_path)])
    assert result.exit_code == 0
    assert "chain" in result.output.lower()


def test_chain_define_and_list_cli(tmp_path: Path) -> None:
    """CLI: chain define from file then list shows it. Skipped if CLI deps missing."""
    pytest.importorskip("yaml")
    from typer.testing import CliRunner
    from workflow_dataset.cli import app
    chain_file = tmp_path / "my_chain.json"
    chain_file.write_text(json.dumps({
        "id": "cli_chain",
        "description": "CLI test chain",
        "steps": [{"id": "s1", "type": "cli", "params": {}}],
    }), encoding="utf-8")
    runner = CliRunner()
    result = runner.invoke(app, ["chain", "define", "--id", "cli_chain", "--file", str(chain_file), "--repo-root", str(tmp_path)])
    assert result.exit_code == 0
    result2 = runner.invoke(app, ["chain", "list", "--repo-root", str(tmp_path)])
    assert result2.exit_code == 0
    assert "cli_chain" in result2.output


# ----- M23A-F2 -----


def test_step_contract_in_definition(tmp_path: Path) -> None:
    """Step contract: expected_inputs, expected_outputs, resumable."""
    definition = {
        "id": "contract_chain",
        "steps": [
            {"id": "s1", "type": "cli", "expected_inputs": ["config"], "expected_outputs": ["stdout"], "resumable": True},
            {"id": "s2", "type": "cli", "resumable": False},
        ],
    }
    save_chain(definition, repo_root=tmp_path)
    loaded = load_chain("contract_chain", repo_root=tmp_path)
    assert loaded["steps"][0].get("expected_inputs") == ["config"]
    assert loaded["steps"][0].get("expected_outputs") == ["stdout"]
    assert loaded["steps"][0].get("resumable") is True
    assert loaded["steps"][1].get("resumable") is False


def test_get_step_by_id_or_index(tmp_path: Path) -> None:
    save_chain({"id": "c1", "steps": [{"id": "verify"}, {"id": "demo"}]}, repo_root=tmp_path)
    defn = load_chain("c1", repo_root=tmp_path)
    out = get_step_by_id_or_index(defn, 0)
    assert out is not None
    assert out[0].get("id") == "verify" and out[1] == 0
    out2 = get_step_by_id_or_index(defn, "demo")
    assert out2 is not None
    assert out2[0].get("id") == "demo" and out2[1] == 1
    assert get_step_by_id_or_index(defn, "missing") is None


def test_get_latest_run_id(tmp_path: Path) -> None:
    assert get_latest_run_id(tmp_path) is None
    save_run_manifest("r1", "c", "", "success", [], "2025-01-01T00:00:00Z", repo_root=tmp_path)
    save_run_manifest("r2", "c", "", "success", [], "2025-01-01T00:00:01Z", repo_root=tmp_path)
    latest = get_latest_run_id(tmp_path)
    assert latest in ("r1", "r2")


def test_resolve_run_id(tmp_path: Path) -> None:
    assert resolve_run_id("nonexistent", tmp_path) is None
    save_run_manifest("rid1", "c", "", "success", [], "2025-01-01T00:00:00Z", repo_root=tmp_path)
    assert resolve_run_id("rid1", tmp_path) == "rid1"
    assert resolve_run_id("latest", tmp_path) == "rid1"


def test_failure_report_section(tmp_path: Path) -> None:
    manifest = {
        "status": "failed",
        "failure_summary": "exit code 1",
        "step_results": [
            {"step_index": 0, "step_id": "s1", "status": "success", "output_paths": ["/out/0.txt"]},
            {"step_index": 1, "step_id": "s2", "status": "failed", "output_paths": []},
        ],
    }
    lines = failure_report_section(manifest, None)
    assert any("Failure report" in line for line in lines)
    assert "Failing step" in "".join(lines)
    assert "1" in "".join(lines)
    assert "Artifacts already produced" in "".join(lines)
    assert "Resume possible" in "".join(lines)
    # With run_id, recommended next commands appear
    lines_with_run = failure_report_section(manifest, None, run_id="my_run_id")
    joined = "".join(lines_with_run)
    assert "Recommended" in joined
    assert "retry-step" in joined
    assert "resume" in joined
    assert "my_run_id" in joined
    assert "s2" in joined


def test_resume_chain(tmp_path: Path) -> None:
    save_chain({"id": "resume_c", "steps": [{"id": "s0"}, {"id": "s1"}]}, repo_root=tmp_path)
    save_run_manifest(
        "resume_run", "resume_c", "", "failed",
        [{"step_index": 0, "step_id": "s0", "status": "success", "output_paths": []}],
        "2025-01-01T00:00:00Z", "2025-01-01T00:00:01Z", "Step 1 failed", repo_root=tmp_path,
    )
    result = resume_chain("resume_run", from_step_index=1, repo_root=tmp_path)
    assert "error" not in result
    assert result.get("run_id") == "resume_run"
    assert len(result.get("step_results") or []) >= 1


def test_retry_step(tmp_path: Path) -> None:
    save_chain({"id": "retry_c", "steps": [{"id": "s0"}]}, repo_root=tmp_path)
    save_run_manifest(
        "retry_run", "retry_c", "", "failed",
        [{"step_index": 0, "step_id": "s0", "status": "failed", "error": "exit 1", "output_paths": []}],
        "2025-01-01T00:00:00Z", "2025-01-01T00:00:01Z", "Step 0 failed", repo_root=tmp_path,
    )
    result = retry_step("retry_run", 0, repo_root=tmp_path)
    assert "error" not in result
    assert result.get("run_id") == "retry_run"


def test_compare_with_output_inventory(tmp_path: Path) -> None:
    save_run_manifest("ia", "c", "v1", "success", [{"step_index": 0, "step_id": "s1", "output_paths": ["/a/1.txt"]}], "2025-01-01T00:00:00Z", "2025-01-01T00:01:00Z", repo_root=tmp_path)
    save_run_manifest("ib", "c", "v2", "success", [{"step_index": 0, "step_id": "s1", "output_paths": ["/b/1.txt"]}], "2025-01-01T00:00:00Z", "2025-01-01T00:02:00Z", repo_root=tmp_path)
    diff = compare_chain_runs("ia", "ib", repo_root=tmp_path, include_artifact_diff=True)
    assert "output_inventory_a" in diff
    assert "output_inventory_b" in diff
    assert len(diff["output_inventory_a"]) == 1 and diff["output_inventory_a"][0]["step_id"] == "s1"
    assert diff.get("artifact_diff") is not None
    assert diff["artifact_diff"]["only_in_a"] == ["/a/1.txt"]
    assert diff["artifact_diff"]["only_in_b"] == ["/b/1.txt"]
    # Timing in run_a / run_b
    assert diff["run_a"].get("started_at") == "2025-01-01T00:00:00Z"
    assert diff["run_a"].get("ended_at") == "2025-01-01T00:01:00Z"
    assert diff["run_b"].get("started_at") == "2025-01-01T00:00:00Z"
    assert diff["run_b"].get("ended_at") == "2025-01-01T00:02:00Z"


def test_report_with_latest(tmp_path: Path) -> None:
    save_run_manifest("latest_run", "c", "", "success", [{"step_index": 0, "step_id": "s1", "status": "success"}], "2025-01-01T00:00:00Z", repo_root=tmp_path)
    report = chain_run_report("latest", repo_root=tmp_path)
    assert "latest_run" in report or "Chain run report" in report
    assert "Run not found" not in report


# ----- M23A-F6: Eval-ready metadata, benchmark hooks, compare benchmark view -----
def test_manifest_has_eval_ready_fields(tmp_path: Path) -> None:
    save_run_manifest(
        "eval_run",
        "template_1",
        "v2",
        "success",
        [
            {"step_index": 0, "step_id": "s1", "status": "success", "output_paths": ["/out/a.txt", "/out/b.txt"]},
        ],
        started_at="2025-01-01T00:00:00Z",
        ended_at="2025-01-01T00:01:30Z",
        repo_root=tmp_path,
    )
    manifest = load_run_manifest("eval_run", tmp_path)
    assert manifest is not None
    assert manifest.get("chain_template_id") == "template_1"
    assert manifest.get("variant_id") == "v2"
    assert manifest.get("final_artifacts") == ["/out/a.txt", "/out/b.txt"]
    assert manifest.get("duration_seconds") == 90.0


def test_list_chain_runs_for_eval(tmp_path: Path) -> None:
    save_run_manifest("er1", "c1", "v1", "success", [], "2025-01-01T00:00:00Z", "2025-01-01T00:00:05Z", repo_root=tmp_path)
    runs = list_chain_runs_for_eval(limit=10, repo_root=tmp_path)
    assert len(runs) >= 1
    r = runs[0]
    assert "run_id" in r and "chain_template_id" in r and "variant_id" in r
    assert "status" in r and "final_artifacts" in r and "duration_seconds" in r
    assert "run_path" in r
    assert r["chain_template_id"] == "c1" and r["variant_id"] == "v1"


def test_get_chain_run_for_eval(tmp_path: Path) -> None:
    save_run_manifest("single_eval", "chain_x", "var_y", "failed", [], "2025-01-01T00:00:00Z", "2025-01-01T00:00:01Z", repo_root=tmp_path)
    r = get_chain_run_for_eval("single_eval", repo_root=tmp_path)
    assert r is not None
    assert r["run_id"] == "single_eval"
    assert r["chain_template_id"] == "chain_x"
    assert r["variant_id"] == "var_y"
    assert r["status"] == "failed"
    assert r["duration_seconds"] == 1.0
    assert get_chain_run_for_eval("nonexistent", repo_root=tmp_path) is None


def test_compare_benchmark_view(tmp_path: Path) -> None:
    save_run_manifest("bva", "c", "v1", "success", [{"step_index": 0, "step_id": "s1", "output_paths": ["/a/1.txt"]}], "2025-01-01T00:00:00Z", "2025-01-01T00:00:10Z", repo_root=tmp_path)
    save_run_manifest("bvb", "c", "v2", "success", [{"step_index": 0, "step_id": "s1", "output_paths": ["/b/1.txt", "/b/2.txt"]}], "2025-01-01T00:00:00Z", "2025-01-01T00:00:20Z", repo_root=tmp_path)
    diff = compare_chain_runs("bva", "bvb", repo_root=tmp_path, benchmark_view=True)
    assert "benchmark_summary" in diff
    bs = diff["benchmark_summary"]
    assert bs["run_id_a"] == "bva" and bs["run_id_b"] == "bvb"
    assert bs["status_a"] == "success" and bs["status_b"] == "success"
    assert bs["duration_seconds_a"] == 10.0 and bs["duration_seconds_b"] == 20.0
    assert bs["artifact_count_a"] == 1 and bs["artifact_count_b"] == 2
    assert "summary_line" in bs
    assert "A=success" in bs["summary_line"] and "B=success" in bs["summary_line"]


def test_benchmark_summary_text(tmp_path: Path) -> None:
    """benchmark_summary_text returns multi-line string when benchmark_summary present."""
    from workflow_dataset.chain_lab.compare import benchmark_summary_text, compare_chain_runs
    save_run_manifest("t1", "c", "v1", "success", [{"step_index": 0, "step_id": "s1", "output_paths": []}], "2025-01-01T00:00:00Z", "2025-01-01T00:00:05Z", repo_root=tmp_path)
    save_run_manifest("t2", "c", "v2", "success", [{"step_index": 0, "step_id": "s1", "output_paths": []}], "2025-01-01T00:00:00Z", "2025-01-01T00:00:10Z", repo_root=tmp_path)
    diff = compare_chain_runs("t1", "t2", repo_root=tmp_path, benchmark_view=True)
    text = benchmark_summary_text(diff)
    assert "t1" in text and "t2" in text
    assert "success" in text
    assert "5.0" in text or "5" in text
    assert "10.0" in text or "10" in text
    assert benchmark_summary_text({}) == ""
    assert benchmark_summary_text({"benchmark_summary": None}) == ""


# ----- M23A-F5: Examples, cleanup, archive -----


def test_list_example_chains() -> None:
    """Bundled examples are listed with id, description, step_count."""
    from workflow_dataset.chain_lab.examples import list_example_chains
    examples = list_example_chains()
    assert isinstance(examples, list)
    for ex in examples:
        assert "id" in ex and "step_count" in ex


def test_get_example_path() -> None:
    """get_example_path returns path for known example id or None for missing."""
    from workflow_dataset.chain_lab.examples import get_example_path, list_example_chains
    examples = list_example_chains()
    if not examples:
        pytest.skip("No bundled examples")
    first_id = examples[0]["id"]
    path = get_example_path(first_id)
    assert path is not None and path.exists()
    assert get_example_path("_nonexistent_example_99_") is None


def test_install_example(tmp_path: Path) -> None:
    """install_example copies example into chains dir."""
    from workflow_dataset.chain_lab.examples import list_example_chains, install_example
    from workflow_dataset.chain_lab.definition import load_chain
    examples = list_example_chains()
    if not examples:
        pytest.skip("No bundled examples")
    first_id = examples[0]["id"]
    path = install_example(first_id, repo_root=tmp_path)
    assert path.exists()
    loaded = load_chain(first_id, repo_root=tmp_path)
    assert loaded["id"] == first_id
    assert len(loaded.get("steps") or []) == examples[0]["step_count"]


def test_list_runs_with_meta(tmp_path: Path) -> None:
    """list_runs_with_meta returns run_id, chain_id, status, started_at."""
    from workflow_dataset.chain_lab.cleanup import list_runs_with_meta
    save_run_manifest("meta_run", "my_chain", "v1", "success", [], "2025-03-16T12:00:00Z", repo_root=tmp_path)
    runs = list_runs_with_meta(repo_root=tmp_path, limit=10)
    assert len(runs) >= 1
    r = next((x for x in runs if x["run_id"] == "meta_run"), None)
    assert r is not None
    assert r["chain_id"] == "my_chain"
    assert r["status"] == "success"
    assert "2025-03-16" in (r.get("started_at") or "")


def test_list_runs_older_than(tmp_path: Path) -> None:
    """list_runs_older_than returns run_ids older than N days."""
    from workflow_dataset.chain_lab.cleanup import list_runs_older_than
    save_run_manifest("old_run", "c", "", "success", [], "2020-01-01T00:00:00Z", repo_root=tmp_path)
    older = list_runs_older_than(repo_root=tmp_path, days=30)
    assert "old_run" in older


def test_archive_run(tmp_path: Path) -> None:
    """archive_run moves run dir to runs/archive/<run_id>."""
    from workflow_dataset.chain_lab.cleanup import archive_run, list_runs_with_meta
    from workflow_dataset.chain_lab.config import get_runs_dir
    save_run_manifest("to_archive", "c", "", "success", [], "2025-01-01T00:00:00Z", repo_root=tmp_path)
    runs_dir = get_runs_dir(tmp_path)
    assert (runs_dir / "to_archive").exists()
    path = archive_run("to_archive", repo_root=tmp_path)
    assert path == runs_dir / "archive" / "to_archive"
    assert not (runs_dir / "to_archive").exists()
    assert (runs_dir / "archive" / "to_archive").exists()
    runs = list_runs_with_meta(repo_root=tmp_path, limit=10)
    run_ids = [r["run_id"] for r in runs]
    assert "to_archive" not in run_ids


def test_cleanup_older_runs_dry_run(tmp_path: Path) -> None:
    """cleanup_older_runs with dry_run only lists run_ids, does not archive."""
    from workflow_dataset.chain_lab.cleanup import cleanup_older_runs
    save_run_manifest("dry_run_old", "c", "", "success", [], "2020-01-01T00:00:00Z", repo_root=tmp_path)
    result = cleanup_older_runs(repo_root=tmp_path, older_than_days=30, dry_run=True, archive=False)
    assert result["dry_run"] is True
    assert "dry_run_old" in result["run_ids"]
    assert result["archived"] == []

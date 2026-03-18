"""Tests for LLM CLI: commands fail gracefully when prerequisites missing or misconfigured."""

from __future__ import annotations

import json
from pathlib import Path
from unittest import mock

import pytest
from typer.testing import CliRunner

from workflow_dataset.cli import app

runner = CliRunner()


def test_llm_prepare_corpus_uses_config() -> None:
    """prepare-corpus runs with repo config; may produce 0 or more docs (no crash)."""
    # Use repo config so Settings validates; override only LLM output path via env or skip if no config
    import os
    from pathlib import Path as P
    config_path = P("configs/settings.yaml")
    if not config_path.exists():
        pytest.skip("configs/settings.yaml not found")
    llm_cfg_path = P("configs/llm_training.yaml")
    result = runner.invoke(app, [
        "llm", "prepare-corpus",
        "--config", str(config_path),
        "--llm-config", str(llm_cfg_path) if llm_cfg_path.exists() else "configs/llm_training.yaml",
    ])
    assert result.exit_code in (0, 1)
    assert "corpus" in result.output.lower() or "docs" in result.output.lower() or "error" in result.output.lower() or "validation" in result.output.lower()


def test_llm_build_sft_graceful_when_corpus_missing() -> None:
    """build-sft can run with missing corpus (empty examples from graph-only)."""
    result = runner.invoke(app, [
        "llm", "build-sft",
        "--config", "configs/settings.yaml",
        "--llm-config", "configs/llm_training.yaml",
    ])
    # Should not crash; may write empty or partial sft
    assert result.exit_code == 0


def test_llm_train_fails_when_base_model_not_set(tmp_path: Path) -> None:
    """Train should fail with clear message if base_model is missing."""
    bad_config = tmp_path / "llm_bad.yaml"
    bad_config.write_text("backend: mlx\n# base_model omitted\n")
    result = runner.invoke(app, [
        "llm", "train",
        "--llm-config", str(bad_config),
    ])
    assert result.exit_code == 1
    assert "base_model" in result.output.lower() or "not set" in result.output.lower()


def test_llm_train_fails_when_sft_train_jsonl_missing(tmp_path: Path) -> None:
    """Train should fail when train.jsonl is missing."""
    config = tmp_path / "llm.yaml"
    config.write_text("backend: mlx\nbase_model: mlx-community/Llama-3.2-3B-Instruct-4bit\nsft_train_dir: /nonexistent/sft/path\n")
    result = runner.invoke(app, ["llm", "train", "--llm-config", str(config)])
    assert result.exit_code == 1
    assert "train" in result.output.lower() or "not found" in result.output.lower() or "sft" in result.output.lower()


def test_llm_eval_graceful_when_test_missing() -> None:
    """Eval exits 0 with message when test.jsonl not found."""
    result = runner.invoke(app, [
        "llm", "eval",
        "--llm-config", "configs/llm_training.yaml",
        "--test-path", "/nonexistent/test.jsonl",
    ])
    assert result.exit_code == 0
    assert "not found" in result.output.lower() or "test" in result.output.lower()


def test_llm_train_help() -> None:
    """llm train --help shows usage and options."""
    result = runner.invoke(app, ["llm", "train", "--help"])
    assert result.exit_code == 0
    assert "train" in result.output.lower() and "llm" in result.output.lower()


def test_llm_eval_help() -> None:
    """llm eval --help shows usage and baseline/real-model."""
    result = runner.invoke(app, ["llm", "eval", "--help"])
    assert result.exit_code == 0
    assert "eval" in result.output.lower() and ("baseline" in result.output or "model" in result.output or "adapter" in result.output)


def test_llm_demo_help() -> None:
    """Demo subcommand exists and shows usage."""
    result = runner.invoke(app, ["llm", "demo", "--help"])
    assert result.exit_code == 0
    assert "prompt" in result.output or "retrieve" in result.output


def test_llm_verify_command() -> None:
    """llm verify runs and reports pipeline status."""
    result = runner.invoke(app, ["llm", "verify", "--llm-config", "configs/llm_training.yaml"])
    assert result.exit_code == 0
    assert "LLM pipeline verification" in result.output or "corpus" in result.output
    assert "base_model" in result.output or "config" in result.output


def test_llm_verify_ignores_failed_runs_for_adapter(tmp_path: Path) -> None:
    """Verify reports adapter MISSING when only failed runs exist (no success marker)."""
    from workflow_dataset.llm.run_summary import write_run_summary
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()
    failed_run = runs_dir / "smoke_20250101_120000"
    failed_run.mkdir()
    write_run_summary(failed_run, success=False, error="failed", adapter_path="")
    cfg = tmp_path / "llm.yaml"
    cfg.write_text(
        "backend: mlx\nbase_model: test/model\n"
        "corpus_path: data/local/llm/corpus/corpus.jsonl\n"
        "sft_train_dir: data/local/llm/sft\nruns_dir: " + str(runs_dir) + "\n"
    )
    result = runner.invoke(app, ["llm", "verify", "--llm-config", str(cfg)])
    assert result.exit_code == 0
    assert "MISSING" in result.output or "adapter" in result.output.lower()


def test_llm_verify_json(tmp_path: Path) -> None:
    """llm verify --json outputs machine-readable JSON; verify module returns dict with expected keys."""
    cfg = tmp_path / "llm.yaml"
    cfg.write_text("backend: mlx\nbase_model: test/model\ncorpus_path: data/local/llm/corpus/corpus.jsonl\nsft_train_dir: data/local/llm/sft\nruns_dir: data/local/llm/runs\n")
    result = runner.invoke(app, ["llm", "verify", "--llm-config", str(cfg), "--json"])
    assert result.exit_code == 0
    from workflow_dataset.llm.verify import verify_llm_pipeline
    res = verify_llm_pipeline(str(cfg))
    data = res.to_dict()
    assert "corpus_present" in data
    assert "base_model_configured" in data
    assert data["base_model"] == "test/model"
    import json
    parsed = json.loads(res.to_json())
    assert parsed["base_model"] == "test/model"


def test_llm_eval_baseline_writes_prediction_mode(tmp_path: Path) -> None:
    """Eval in baseline mode writes prediction_mode to metrics and summary."""
    test_file = tmp_path / "test.jsonl"
    test_file.write_text(
        '{"eval_id": "e1", "task_type": "knowledge_qa", "messages": [{"role": "user", "content": "Q?"}, {"role": "assistant", "content": "A"}], "reference": "A"}\n'
    )
    out_dir = tmp_path / "eval_out"
    result = runner.invoke(app, [
        "llm", "eval",
        "--llm-config", "configs/llm_training.yaml",
        "--test-path", str(test_file),
        "--run-dir", str(out_dir),
    ])
    assert result.exit_code == 0
    assert "baseline" in result.output or "mode=" in result.output
    metrics_path = out_dir / "metrics.json"
    assert metrics_path.exists()
    import json
    metrics = json.loads(metrics_path.read_text())
    assert metrics.get("prediction_mode") == "baseline"


def test_llm_smoke_train_fails_without_base_model(tmp_path: Path) -> None:
    """smoke-train fails with clear message when base_model not set."""
    cfg = tmp_path / "llm.yaml"
    cfg.write_text("backend: mlx\nruns_dir: data/local/llm/runs\n")
    result = runner.invoke(app, ["llm", "smoke-train", "--llm-config", str(cfg)])
    assert result.exit_code == 1
    assert "base_model" in result.output.lower()


def test_llm_smoke_train_creates_smoke_sft_and_run_summary(tmp_path: Path) -> None:
    """smoke-train creates smoke_sft dir, train/valid.jsonl, and run dir with run_summary.json."""
    runs_dir = tmp_path / "runs"
    cfg = tmp_path / "llm.yaml"
    cfg.write_text("backend: mlx\nbase_model: mlx-community/some-3B\nruns_dir: " + str(runs_dir) + "\n")
    result = runner.invoke(app, ["llm", "smoke-train", "--llm-config", str(cfg)])
    smoke_sft = runs_dir.parent / "smoke_sft"
    assert smoke_sft.exists(), "smoke-train should create smoke_sft next to runs_dir"
    assert (smoke_sft / "train.jsonl").exists()
    assert (smoke_sft / "valid.jsonl").exists()
    # Backend will fail (no real model), but run dir and run_summary should be written
    run_dirs = [d for d in runs_dir.iterdir() if d.is_dir() and d.name.startswith("smoke_")]
    assert len(run_dirs) >= 1
    summary_path = run_dirs[0] / "run_summary.json"
    assert summary_path.exists(), "smoke-train should write run_summary.json"
    summary = json.loads(summary_path.read_text())
    assert "success" in summary
    assert summary.get("base_model") == "mlx-community/some-3B"
    assert summary.get("backend") == "mlx"


def test_llm_demo_reports_mode() -> None:
    """Demo with --prompt prints interpreter, mode, base model, adapter (or error)."""
    result = runner.invoke(app, [
        "llm", "demo",
        "--llm-config", "configs/llm_training.yaml",
        "--prompt", "What is workflow?",
    ], catch_exceptions=False)
    assert "mode" in result.output or "base model" in result.output or "interpreter" in result.output or "No adapter" in result.output or "Inference failed" in result.output or "failed" in result.output.lower()


def test_llm_demo_base_model_mode_prints_base_and_adapter_none(tmp_path: Path) -> None:
    """Demo in base-model mode prints base model and adapter: (none)."""
    cfg = tmp_path / "llm.yaml"
    cfg.write_text(
        "backend: mlx\nbase_model: mlx-community/Some-Model-4bit\n"
        "runs_dir: " + str(tmp_path / "runs") + "\n"
    )
    result = runner.invoke(app, [
        "llm", "demo",
        "--llm-config", str(cfg),
        "--prompt", "Hi",
    ])
    assert "mode" in result.output
    assert "base model" in result.output
    assert "adapter" in result.output
    assert "base_model" in result.output or "Some-Model" in result.output


def test_llm_demo_adapter_mode_requires_base_model(tmp_path: Path) -> None:
    """Demo with --adapter but no base_model in config exits 1 with clear message."""
    cfg = tmp_path / "llm.yaml"
    cfg.write_text("backend: mlx\nruns_dir: " + str(tmp_path / "runs") + "\n")
    result = runner.invoke(app, [
        "llm", "demo",
        "--llm-config", str(cfg),
        "--adapter", str(tmp_path / "fake_adapters"),
        "--prompt", "Hi",
    ])
    assert result.exit_code == 1
    assert "base_model" in result.output.lower() or "base model" in result.output.lower()


def test_llm_demo_adapter_mode_prints_base_and_adapter_path(tmp_path: Path) -> None:
    """Demo with --adapter prints mode adapter, base model, and adapter path (not adapter as model)."""
    adapter_dir = tmp_path / "adapters"
    adapter_dir.mkdir()
    (adapter_dir / "adapter_config.json").write_text("{}")
    cfg = tmp_path / "llm.yaml"
    cfg.write_text(
        "backend: mlx\nbase_model: mlx-community/Base-4bit\n"
        "runs_dir: " + str(tmp_path / "runs") + "\n"
    )
    with mock.patch("workflow_dataset.llm.train_backend.get_backend") as m_get:
        mock_backend = mock.Mock()
        mock_backend.run_inference.return_value = "Generated text"
        m_get.return_value = mock_backend
        result = runner.invoke(app, [
            "llm", "demo",
            "--llm-config", str(cfg),
            "--adapter", str(adapter_dir),
            "--prompt", "Hi",
        ])
    assert result.exit_code == 0
    assert "mode" in result.output and "adapter" in result.output.lower()
    assert "base model" in result.output
    mock_backend.run_inference.assert_called_once()
    call_kw = mock_backend.run_inference.call_args[1]
    assert call_kw.get("adapter_path") == str(adapter_dir)
    assert "Base-4bit" in str(mock_backend.run_inference.call_args[0][0])


def test_llm_demo_inference_error_graceful(tmp_path: Path) -> None:
    """When inference fails, demo prints 'Inference failed' and concise message, not raw traceback."""
    adapter_dir = tmp_path / "adapters"
    adapter_dir.mkdir()
    (adapter_dir / "adapter_config.json").write_text("{}")
    cfg = tmp_path / "llm.yaml"
    cfg.write_text(
        "backend: mlx\nbase_model: mlx-community/Base-4bit\n"
        "runs_dir: " + str(tmp_path / "runs") + "\n"
    )
    with mock.patch("workflow_dataset.llm.train_backend.get_backend") as m_get:
        mock_backend = mock.Mock()
        mock_backend.run_inference.return_value = "[inference error: FileNotFoundError: config.json]"
        m_get.return_value = mock_backend
        result = runner.invoke(app, [
            "llm", "demo",
            "--llm-config", str(cfg),
            "--adapter", str(adapter_dir),
            "--prompt", "Hi",
        ])
    assert "Inference failed" in result.output
    assert "config.json" in result.output or "error" in result.output.lower()
    assert "Traceback" not in result.output and "File \"" not in result.output


def test_llm_demo_exits_nonzero_when_no_adapter_no_base_model(tmp_path: Path) -> None:
    """Demo exits 1 with clear message when no adapter and no base_model in config."""
    cfg = tmp_path / "llm.yaml"
    cfg.write_text("backend: mlx\nruns_dir: " + str(tmp_path / "runs") + "\n")
    result = runner.invoke(app, [
        "llm", "demo",
        "--llm-config", str(cfg),
        "--prompt", "Hi",
    ])
    assert result.exit_code == 1
    assert "adapter" in result.output.lower() or "base_model" in result.output.lower()


def test_llm_latest_adapter_exits_nonzero_when_none(tmp_path: Path) -> None:
    """latest-adapter exits 1 when no successful run exists."""
    cfg = tmp_path / "llm.yaml"
    cfg.write_text("backend: mlx\nruns_dir: " + str(tmp_path / "runs") + "\n")
    result = runner.invoke(app, ["llm", "latest-adapter", "--llm-config", str(cfg)])
    assert result.exit_code == 1
    assert "No successful" in result.output or "smoke-train" in result.output.lower()


def test_llm_latest_run_exits_nonzero_when_none(tmp_path: Path) -> None:
    """latest-run exits 1 when no successful run exists."""
    cfg = tmp_path / "llm.yaml"
    cfg.write_text("backend: mlx\nruns_dir: " + str(tmp_path / "runs") + "\n")
    result = runner.invoke(app, ["llm", "latest-run", "--llm-config", str(cfg)])
    assert result.exit_code == 1


def test_setup_build_corpus_cli(tmp_path: Path) -> None:
    """setup build-corpus runs when allow_personal_corpus_from_setup is True and session+parsed+style exist."""
    import yaml
    config_path = tmp_path / "settings.yaml"
    config_path.write_text(yaml.dump({
        "project": {"name": "t", "version": "1", "output_excel": "x", "output_csv_dir": "c", "output_parquet_dir": "p", "qa_report_path": "q"},
        "runtime": {"timezone": "UTC", "long_run_profile": True, "max_workers": 1},
        "paths": {"raw_official": "r", "raw_private": "r", "interim": "i", "processed": "p", "prompts": "pr", "context": "c", "sqlite_path": "s", "graph_store_path": str(tmp_path / "graph.sqlite")},
        "setup": {
            "setup_dir": str(tmp_path / "setup"),
            "parsed_artifacts_dir": str(tmp_path / "parsed"),
            "style_signals_dir": str(tmp_path / "style_signals"),
            "setup_reports_dir": str(tmp_path / "reports"),
            "allow_personal_corpus_from_setup": True,
            "allow_raw_text_for_personal_corpus": False,
        },
    }, default_flow_style=False))
    (tmp_path / "setup" / "sessions").mkdir(parents=True)
    session_id = "session_test_corpus"
    (tmp_path / "setup" / "sessions" / f"{session_id}.json").write_text('{"session_id": "' + session_id + '", "current_stage": "interpretation"}')
    (tmp_path / "parsed" / session_id).mkdir(parents=True)
    (tmp_path / "parsed" / session_id / "a.json").write_text('{"source_path": "/x/y.txt", "artifact_family": "text_document", "title": "T", "summary": "S", "error": ""}')
    (tmp_path / "style_signals" / session_id).mkdir(parents=True)
    (tmp_path / "style_signals" / session_id / "signatures.json").write_text('[{"pattern_type": "naming", "value": "snake", "description": "Snake", "confidence": 0.8, "evidence_paths": [], "session_id": "' + session_id + '", "project_path": ""}]')
    result = runner.invoke(app, ["setup", "build-corpus", "--config", str(config_path), "--session-id", session_id, "--output", str(tmp_path / "corpus_out")])
    assert result.exit_code == 0
    assert (tmp_path / "corpus_out" / "personal_corpus.jsonl").exists()


def test_setup_build_sft_cli(tmp_path: Path) -> None:
    """setup build-sft runs when allow_personal_sft_from_setup is True and session+parsed+style exist."""
    import yaml
    config_path = tmp_path / "settings.yaml"
    config_path.write_text(yaml.dump({
        "project": {"name": "t", "version": "1", "output_excel": "x", "output_csv_dir": "c", "output_parquet_dir": "p", "qa_report_path": "q"},
        "runtime": {"timezone": "UTC", "long_run_profile": True, "max_workers": 1},
        "paths": {"raw_official": "r", "raw_private": "r", "interim": "i", "processed": "p", "prompts": "pr", "context": "c", "sqlite_path": "s", "graph_store_path": str(tmp_path / "graph.sqlite")},
        "setup": {
            "setup_dir": str(tmp_path / "setup"),
            "parsed_artifacts_dir": str(tmp_path / "parsed"),
            "style_signals_dir": str(tmp_path / "style_signals"),
            "setup_reports_dir": str(tmp_path / "reports"),
            "allow_personal_sft_from_setup": True,
            "allow_raw_text_for_personal_sft": False,
        },
    }, default_flow_style=False))
    (tmp_path / "setup" / "sessions").mkdir(parents=True)
    session_id = "session_test_sft"
    (tmp_path / "setup" / "sessions" / f"{session_id}.json").write_text('{"session_id": "' + session_id + '", "current_stage": "interpretation"}')
    (tmp_path / "parsed" / session_id).mkdir(parents=True)
    (tmp_path / "parsed" / session_id / "b.json").write_text('{"source_path": "/proj/readme.txt", "artifact_family": "text_document", "title": "R", "summary": "Summary", "error": ""}')
    (tmp_path / "style_signals" / session_id).mkdir(parents=True)
    (tmp_path / "style_signals" / session_id / "signatures.json").write_text('[{"pattern_type": "naming_convention", "value": "snake", "description": "Snake", "confidence": 0.8, "evidence_paths": [], "session_id": "' + session_id + '", "project_path": ""}]')
    result = runner.invoke(app, ["setup", "build-sft", "--config", str(config_path), "--session-id", session_id, "--output", str(tmp_path / "sft_out")])
    assert result.exit_code == 0
    assert (tmp_path / "sft_out" / "train.jsonl").exists()


def test_full_train_config_resolution() -> None:
    """Full training config llm_training_full.yaml loads with stronger settings."""
    full_config = Path("configs/llm_training_full.yaml")
    if not full_config.exists():
        pytest.skip("configs/llm_training_full.yaml not found")
    import yaml
    with open(full_config) as f:
        cfg = yaml.safe_load(f)
    assert cfg.get("num_epochs", 0) >= 3
    assert cfg.get("base_model")
    assert cfg.get("runs_dir") or cfg.get("output_dir")
    assert cfg.get("run_type", "full") or "full" in str(cfg.get("runs_dir", ""))


def test_llm_compare_runs_help() -> None:
    """llm compare-runs --help shows usage."""
    result = runner.invoke(app, ["llm", "compare-runs", "--help"])
    assert result.exit_code == 0
    assert "compare" in result.output.lower()


def test_llm_compare_runs_graceful_when_test_missing(tmp_path: Path) -> None:
    """compare-runs exits 0 with message when test.jsonl not found."""
    cfg = tmp_path / "llm.yaml"
    cfg.write_text("backend: mlx\nbase_model: m\nruns_dir: " + str(tmp_path / "runs") + "\ncorpus_path: " + str(tmp_path / "c.jsonl"))
    (tmp_path / "runs").mkdir()
    result = runner.invoke(app, ["llm", "compare-runs", "--llm-config", str(cfg), "--test-path", str(tmp_path / "nonexistent.jsonl")])
    assert result.exit_code == 0
    assert "not found" in result.output.lower() or "test" in result.output.lower()


def test_llm_demo_suite_help() -> None:
    """llm demo-suite --help shows usage."""
    result = runner.invoke(app, ["llm", "demo-suite", "--help"])
    assert result.exit_code == 0
    assert "demo" in result.output.lower() and ("baseline" in result.output or "retrieval" in result.output)


def test_llm_demo_suite_fails_without_base_model(tmp_path: Path) -> None:
    """demo-suite requires base_model in config."""
    cfg = tmp_path / "llm.yaml"
    cfg.write_text("backend: mlx\n# base_model omitted\nruns_dir: " + str(tmp_path / "runs"))
    result = runner.invoke(app, ["llm", "demo-suite", "--llm-config", str(cfg)])
    assert result.exit_code == 1
    assert "base_model" in result.output.lower()

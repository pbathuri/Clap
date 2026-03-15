"""Tests for LLM CLI: commands fail gracefully when prerequisites missing or misconfigured."""

from __future__ import annotations

from pathlib import Path

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


def test_llm_demo_help() -> None:
    """Demo subcommand exists and shows usage."""
    result = runner.invoke(app, ["llm", "demo", "--help"])
    assert result.exit_code == 0
    assert "prompt" in result.output or "retrieve" in result.output


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

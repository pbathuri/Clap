"""
LLM pipeline verification: report training data, config, backend, adapters, eval, and demo readiness.

Machine-readable and human-readable output for debugging and CI.
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class VerifyResult:
    """Structured verification result."""

    corpus_present: bool = False
    corpus_path: str = ""
    corpus_count: int = 0
    sft_train_present: bool = False
    sft_val_present: bool = False
    sft_test_present: bool = False
    sft_dir: str = ""
    sft_train_count: int = 0
    sft_test_count: int = 0
    config_present: bool = False
    config_path: str = ""
    base_model_configured: bool = False
    base_model: str = ""
    backend_deps_available: bool = False
    backend: str = ""
    runs_dir: str = ""
    run_dirs_count: int = 0
    adapter_artifacts_present: bool = False
    adapter_paths: list[str] = field(default_factory=list)
    latest_run_dir: str = ""
    eval_outputs_present: bool = False
    eval_predictions_path: str = ""
    eval_metrics_path: str = ""
    eval_uses_real_model: bool = False
    demo_can_load_adapter: bool = False
    demo_adapter_path: str = ""
    demo_can_load_base: bool = False
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


def _count_lines(path: Path) -> int:
    if not path.exists():
        return 0
    try:
        with open(path, "r", encoding="utf-8") as f:
            return sum(1 for _ in f)
    except Exception:
        return 0


def _check_mlx_lm() -> bool:
    try:
        r = subprocess.run(
            [sys.executable, "-m", "mlx_lm.lora", "--help"],
            capture_output=True,
            timeout=10,
        )
        return r.returncode == 0
    except Exception:
        return False


def _find_latest_adapter_run(runs_dir: Path) -> tuple[int, str, list[str]]:
    """Return (run_dirs_count, latest_successful_run_dir, list of successful adapter paths)."""
    from workflow_dataset.llm.run_summary import find_all_successful_adapters, find_latest_successful_adapter

    if not runs_dir.exists():
        return 0, "", []
    run_dirs_count = sum(1 for d in runs_dir.iterdir() if d.is_dir())
    all_success = find_all_successful_adapters(runs_dir)
    adapter_paths = [a for a, _ in all_success]
    _, latest_run = find_latest_successful_adapter(runs_dir)
    return run_dirs_count, latest_run, adapter_paths


def _find_eval_outputs(runs_dir: Path) -> tuple[bool, str, str]:
    """Check for eval_out or any run with predictions.jsonl / metrics.json."""
    if not runs_dir.exists():
        return False, "", ""
    eval_dir = runs_dir / "eval_out"
    if eval_dir.exists():
        pred = eval_dir / "predictions.jsonl"
        metrics = eval_dir / "metrics.json"
        return pred.exists(), str(pred) if pred.exists() else "", str(metrics) if metrics.exists() else ""
    for d in runs_dir.iterdir():
        if d.is_dir():
            pred = d / "predictions.jsonl"
            if pred.exists():
                return True, str(pred), str(d / "metrics.json")
    return False, "", ""


def verify_llm_pipeline(
    llm_config_path: str | Path,
    config_dict: dict[str, Any] | None = None,
) -> VerifyResult:
    """
    Run all checks and return VerifyResult.
    If config_dict is provided, use it; else load from llm_config_path.
    """
    path = Path(llm_config_path)
    result = VerifyResult()
    if path.exists():
        result.config_present = True
        result.config_path = str(path.resolve())
        if config_dict is None:
            try:
                import yaml
                with open(path, "r", encoding="utf-8") as f:
                    config_dict = yaml.safe_load(f) or {}
            except Exception as e:
                result.errors.append(f"config load: {e}")
                config_dict = {}
    else:
        result.errors.append(f"config not found: {path}")
        config_dict = config_dict or {}

    repo_root = Path.cwd()
    if path.exists():
        try:
            resolved = path.resolve()
            if resolved.parent.name == "configs":
                repo_root = resolved.parent.parent
            else:
                repo_root = resolved.parent
        except Exception:
            pass
    corpus_path = Path(config_dict.get("corpus_path", "data/local/llm/corpus/corpus.jsonl"))
    if not corpus_path.is_absolute():
        corpus_path = repo_root / corpus_path
    result.corpus_path = str(corpus_path)
    if corpus_path.exists():
        result.corpus_present = True
        result.corpus_count = _count_lines(corpus_path)

    sft_dir = config_dict.get("sft_train_dir", "data/local/llm/sft")
    sft_path = Path(sft_dir)
    if not sft_path.is_absolute():
        sft_path = repo_root / sft_dir
    result.sft_dir = str(sft_path)
    train_file = sft_path / "train.jsonl"
    val_file = sft_path / "val.jsonl"
    test_file = sft_path / "test.jsonl"
    result.sft_train_present = train_file.exists()
    result.sft_val_present = val_file.exists()
    result.sft_test_present = test_file.exists()
    result.sft_train_count = _count_lines(train_file)
    result.sft_test_count = _count_lines(test_file)

    result.base_model = config_dict.get("base_model", "")
    result.base_model_configured = bool(result.base_model)
    result.backend = config_dict.get("backend", "mlx")
    result.backend_deps_available = _check_mlx_lm() if result.backend == "mlx" else False

    runs_dir = Path(config_dict.get("runs_dir", "data/local/llm/runs"))
    if not runs_dir.is_absolute():
        runs_dir = repo_root / config_dict.get("runs_dir", "data/local/llm/runs")
    result.runs_dir = str(runs_dir)
    run_dirs_count, latest_run, adapter_paths = _find_latest_adapter_run(runs_dir)
    result.run_dirs_count = run_dirs_count
    result.latest_run_dir = latest_run
    result.adapter_paths = adapter_paths
    result.adapter_artifacts_present = len(adapter_paths) > 0
    result.demo_can_load_adapter = result.adapter_artifacts_present
    if adapter_paths:
        result.demo_adapter_path = adapter_paths[-1]
    result.demo_can_load_base = result.base_model_configured and result.backend_deps_available

    eval_ok, pred_path, metrics_path = _find_eval_outputs(runs_dir)
    result.eval_outputs_present = eval_ok
    result.eval_predictions_path = pred_path
    result.eval_metrics_path = metrics_path
    if result.eval_metrics_path and Path(result.eval_metrics_path).exists():
        try:
            with open(result.eval_metrics_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            result.eval_uses_real_model = meta.get("prediction_mode") == "real_model"
        except Exception:
            pass
    return result

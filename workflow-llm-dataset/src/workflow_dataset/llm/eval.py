"""
Evaluate model on held-out examples: exact match, token overlap, top-k, explanation heuristics.

Supports model-only and retrieval+model modes. Saves per-example predictions and aggregate metrics.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Callable

from workflow_dataset.llm.schemas import EvalExample, EvalResult


def _tokenize(s: str) -> set[str]:
    return set(re.findall(r"\w+", s.lower()))


def exact_match(pred: str, ref: str) -> float:
    """1.0 if pred strip equals ref strip (or ref_short), else 0."""
    p = pred.strip()
    r = ref.strip()
    return 1.0 if p and r and p == r else 0.0


def token_overlap(pred: str, ref: str) -> float:
    """ROUGE-lite: F1 of token overlap."""
    tp = _tokenize(pred)
    tr = _tokenize(ref)
    if not tr:
        return 1.0 if not tp else 0.0
    overlap = len(tp & tr)
    prec = overlap / len(tp) if tp else 0.0
    rec = overlap / len(tr)
    if prec + rec == 0:
        return 0.0
    return 2 * prec * rec / (prec + rec)


def top_k_hit(pred: str, ref_options: list[str], k: int = 3) -> float:
    """1.0 if ref (or ref_short) appears in top-k inferred from pred (e.g. first line), else 0."""
    if not ref_options:
        return 0.0
    first_line = pred.strip().split("\n")[0].lower() if pred else ""
    for ref in ref_options[:k]:
        if ref.strip().lower() in first_line or first_line in ref.strip().lower():
            return 1.0
    return 0.0


def explanation_completeness(pred: str, min_words: int = 10) -> float:
    """Heuristic: 1.0 if pred has at least min_words and contains explanation-like tokens."""
    words = pred.strip().split()
    if len(words) < min_words:
        return 0.0
    low = pred.lower()
    if any(x in low for x in ("because", "based on", "suggest", "pattern", "observed", "workflow", "project")):
        return 1.0
    return 0.5


def compute_metrics(
    predictions: list[dict[str, Any]],
    task_type_metrics: dict[str, list[str]] | None = None,
) -> dict[str, float]:
    """
    predictions: list of {eval_id, task_type, reference, reference_short, predicted, ...}.
    task_type_metrics: optional map task_type -> [exact_match, token_overlap, ...].
    """
    if not predictions:
        return {}
    task_type_metrics = task_type_metrics or {
        "knowledge_qa": ["token_overlap", "explanation_completeness"],
        "workflow_inference": ["token_overlap", "explanation_completeness"],
        "routine_interpretation": ["token_overlap", "explanation_completeness"],
        "suggestion_justification": ["token_overlap", "explanation_completeness"],
        "next_step_suggestion": ["token_overlap", "explanation_completeness"],
        "safety_boundary": ["exact_match", "token_overlap"],
    }
    scores: dict[str, list[float]] = {}
    for ex in predictions:
        pred = ex.get("predicted", "")
        ref = ex.get("reference", "") or ""
        ref_short = ex.get("reference_short", "") or ref
        task = ex.get("task_type", "default")
        metrics = task_type_metrics.get(task, ["token_overlap"])
        for m in metrics:
            if m == "exact_match":
                v = exact_match(pred, ref_short or ref)
            elif m == "token_overlap":
                v = token_overlap(pred, ref)
            elif m == "explanation_completeness":
                v = explanation_completeness(pred)
            else:
                continue
            key = m
            scores.setdefault(key, []).append(v)
    return {k: sum(v) / len(v) if v else 0.0 for k, v in scores.items()}


def run_eval(
    test_path: Path | str,
    predict_fn: Callable[[dict[str, Any]], str],
    output_dir: Path | str,
    run_id: str = "",
    model_id: str = "",
    retrieval_used: bool = False,
) -> EvalResult:
    """
    Load test JSONL, run predict_fn on each example, compute metrics, save predictions and metrics.
    predict_fn(ex) -> predicted string. ex has keys: eval_id, task_type, messages, reference, reference_short, ...
    """
    test_path = Path(test_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    predictions: list[dict[str, Any]] = []
    if not test_path.exists():
        return EvalResult(
            run_id=run_id,
            model_id=model_id,
            retrieval_used=retrieval_used,
            metrics={},
            num_examples=0,
            predictions_path="",
        )
    with open(test_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            ex = json.loads(line)
            if ex.get("reference") is None and ex.get("messages"):
                for m in reversed(ex["messages"]):
                    if m.get("role") == "assistant":
                        ex["reference"] = m.get("content", "")
                        break
            pred = predict_fn(ex)
            ex["predicted"] = pred
            predictions.append(ex)
    metrics = compute_metrics(predictions)
    pred_path = output_dir / "predictions.jsonl"
    with open(pred_path, "w", encoding="utf-8") as f:
        for ex in predictions:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")
    metrics_path = output_dir / "metrics.json"
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    summary_path = output_dir / "eval_summary.md"
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(f"# Eval summary\n\nRun: {run_id}\nModel: {model_id}\nRetrieval: {retrieval_used}\n\n")
        f.write("## Metrics\n\n")
        for k, v in metrics.items():
            f.write(f"- **{k}**: {v:.4f}\n")
        f.write(f"\nTotal examples: {len(predictions)}\n")
    return EvalResult(
        run_id=run_id,
        model_id=model_id,
        retrieval_used=retrieval_used,
        metrics=metrics,
        num_examples=len(predictions),
        predictions_path=str(pred_path),
        details={"metrics_path": str(metrics_path), "summary_path": str(summary_path)},
    )

"""
Compare baseline, smoke adapter, and full adapter across retrieval off/on.
Produces machine-readable metrics and a readable comparison markdown report.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from workflow_dataset.llm.eval import run_eval, _messages_to_prompt
from workflow_dataset.llm.run_summary import (
    find_latest_successful_adapter_by_type,
    get_run_type,
)
from workflow_dataset.llm.schemas import EvalResult


def _baseline_predict(_ex: dict) -> str:
    for m in reversed(_ex.get("messages", [])):
        if m.get("role") == "assistant":
            return m.get("content", "")
    return ""


def run_comparison(
    llm_config: dict[str, Any],
    test_path: Path,
    runs_dir: Path,
    output_dir: Path | None = None,
    *,
    corpus_path: str = "",
    retrieval_top_k: int = 5,
    skip_missing: bool = True,
) -> dict[str, Any]:
    """
    Run eval for baseline, smoke adapter, full adapter; each with retrieval off and on.
    Writes per-slice outputs under output_dir (default runs_dir / "comparison_YYYYMMDD_HHMMSS")
    and comparison_latest.json + comparison_latest.md in runs_dir.
    Returns aggregate dict with slices and summary.
    """
    runs_dir = Path(runs_dir)
    test_path = Path(test_path)
    if not test_path.exists():
        return {"error": "test_path not found", "slices": []}
    out = output_dir or (runs_dir / ("comparison_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")))
    out.mkdir(parents=True, exist_ok=True)
    corpus_path = corpus_path or llm_config.get("corpus_path", "data/local/llm/corpus/corpus.jsonl")
    backend_name = llm_config.get("backend", "mlx")
    base_model = llm_config.get("base_model", "")
    max_tokens = int(llm_config.get("max_seq_length", 2048) // 4)

    from workflow_dataset.llm.train_backend import get_backend
    backend = get_backend(backend_name)

    slices: list[dict[str, Any]] = []
    slice_ids = [
        ("baseline", False, None, "baseline"),
        ("baseline_retrieval", True, None, "baseline"),
        ("smoke", False, "smoke", "smoke"),
        ("smoke_retrieval", True, "smoke", "smoke"),
        ("full", False, "full", "full"),
        ("full_retrieval", True, "full", "full"),
    ]
    for slice_id, retrieval, run_type, adapter_type in slice_ids:
        slice_dir = out / slice_id
        slice_dir.mkdir(parents=True, exist_ok=True)
        if adapter_type == "baseline":
            predict_fn: Callable[[dict], str] = _baseline_predict
            run_id = "baseline_retrieval" if retrieval else "baseline"
            model_id = "n/a"
            prediction_mode = "baseline"
        else:
            adapter_path, run_dir_str = find_latest_successful_adapter_by_type(runs_dir, run_type)
            if not adapter_path and skip_missing:
                slices.append({
                    "slice_id": slice_id,
                    "skipped": True,
                    "reason": f"no {run_type} adapter found",
                })
                continue
            if not adapter_path:
                slices.append({"slice_id": slice_id, "skipped": True, "reason": f"no {run_type} adapter"})
                continue

            def make_predict(adapter: str, use_retrieval: bool):
                def _predict(ex: dict) -> str:
                    prompt = _messages_to_prompt(ex.get("messages", []))
                    if not prompt:
                        return ""
                    if use_retrieval and Path(corpus_path).exists():
                        from workflow_dataset.llm.retrieval_context import retrieve, format_context_for_prompt
                        docs = retrieve(corpus_path, prompt, top_k=retrieval_top_k)
                        ctx = format_context_for_prompt(docs, max_chars=2000)
                        if ctx:
                            prompt = "Context (retrieved):\n" + ctx + "\n\nUser: " + prompt
                    return backend.run_inference(base_model, prompt, max_tokens=max_tokens, adapter_path=adapter)
                return _predict

            predict_fn = make_predict(adapter_path, retrieval)
            run_id = f"{run_type}_retrieval" if retrieval else run_type
            model_id = adapter_path
            prediction_mode = "real_model"

        result = run_eval(
            test_path,
            predict_fn,
            slice_dir,
            run_id=run_id,
            model_id=model_id,
            retrieval_used=retrieval,
            prediction_mode=prediction_mode,
        )
        slices.append({
            "slice_id": slice_id,
            "run_id": result.run_id,
            "model_id": result.model_id,
            "retrieval_used": result.retrieval_used,
            "prediction_mode": result.prediction_mode,
            "num_examples": result.num_examples,
            "metrics": result.metrics,
            "predictions_path": result.predictions_path,
        })

    payload = {
        "comparison_time": datetime.now(timezone.utc).isoformat(),
        "test_path": str(test_path),
        "output_dir": str(out),
        "slices": slices,
    }
    latest_json = runs_dir / "comparison_latest.json"
    with open(latest_json, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    report_path = _write_comparison_md(runs_dir, payload)
    payload["report_path"] = str(report_path)

    # Persist quality_report.md into latest full run dir if we have full slice
    full_adapter_path, full_run_dir = find_latest_successful_adapter_by_type(runs_dir, "full")
    if full_run_dir and any(s.get("slice_id") == "full" and not s.get("skipped") for s in slices):
        full_slice = next((s for s in slices if s.get("slice_id") == "full" and not s.get("skipped")), None)
        full_ret_slice = next((s for s in slices if s.get("slice_id") == "full_retrieval" and not s.get("skipped")), None)
        retrieval_impact = None
        if full_slice and full_ret_slice and full_slice.get("metrics") and full_ret_slice.get("metrics"):
            to_off = full_slice["metrics"].get("token_overlap", 0)
            to_on = full_ret_slice["metrics"].get("token_overlap", 0)
            retrieval_impact = f"token_overlap: retrieval_off={to_off:.4f}, retrieval_on={to_on:.4f} (Δ {to_on - to_off:+.4f})"
        from workflow_dataset.llm.quality_report import write_quality_report
        write_quality_report(
            Path(full_run_dir),
            comparison_slice=full_slice,
            retrieval_impact=retrieval_impact,
            recommendation="Review comparison_latest.md and iterate on data/prompts if needed.",
        )
    return payload


def _write_comparison_md(runs_dir: Path, payload: dict[str, Any]) -> Path:
    report_path = runs_dir / "comparison_latest.md"
    lines = [
        "# LLM comparison report",
        "",
        f"Generated: {payload.get('comparison_time', '')}",
        f"Test set: {payload.get('test_path', '')}",
        f"Output dir: {payload.get('output_dir', '')}",
        "",
        "## Slices",
        "",
    ]
    for s in payload.get("slices", []):
        if s.get("skipped"):
            lines.append(f"- **{s['slice_id']}**: skipped — {s.get('reason', '')}")
            continue
        lines.append(f"- **{s['slice_id']}** (retrieval={s.get('retrieval_used', False)})")
        lines.append(f"  - examples: {s.get('num_examples', 0)}")
        for k, v in (s.get("metrics") or {}).items():
            if isinstance(v, (int, float)):
                lines.append(f"  - {k}: {v:.4f}" if isinstance(v, float) else f"  - {k}: {v}")
        lines.append("")
    lines.append("## Retrieval impact")
    by_base = {}
    for s in payload.get("slices", []):
        if s.get("skipped"):
            continue
        base = s["slice_id"].replace("_retrieval", "")
        by_base.setdefault(base, []).append(s)
    for base, parts in by_base.items():
        if len(parts) != 2:
            continue
        off = next((p for p in parts if not p.get("retrieval_used")), None)
        on = next((p for p in parts if p.get("retrieval_used")), None)
        if off and on and off.get("metrics") and on.get("metrics"):
            tok_off = off["metrics"].get("token_overlap", 0)
            tok_on = on["metrics"].get("token_overlap", 0)
            diff = tok_on - tok_off
            lines.append(f"- **{base}**: token_overlap retrieval_off={tok_off:.4f} retrieval_on={tok_on:.4f} (Δ {diff:+.4f})")
    lines.append("")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return report_path

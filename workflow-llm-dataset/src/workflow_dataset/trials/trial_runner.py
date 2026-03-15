"""
M17: Run a workflow trial in a given mode; produce result and optional bundle.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.utils.hashes import stable_id
from workflow_dataset.trials.trial_models import (
    WorkflowTrial,
    WorkflowTrialResult,
    TrialMode,
)
from workflow_dataset.trials.trial_scoring import score_result


def run_trial(
    trial: WorkflowTrial,
    mode: TrialMode,
    *,
    context_bundle: dict[str, Any],
    llm_config: dict[str, Any] | None = None,
    adapter_path: str | Path | None = None,
    corpus_path: str | Path | None = None,
    retrieval_top_k: int = 5,
    output_dir: Path | str | None = None,
) -> WorkflowTrialResult:
    """
    Run a single trial in the given mode. Uses context_bundle for prompt; optionally LLM + adapter + retrieval.
    Persists result to output_dir if set. Returns WorkflowTrialResult.
    """
    output_dir = Path(output_dir) if output_dir else None
    retrieval_used = mode in (TrialMode.RETRIEVAL_ONLY, TrialMode.ADAPTER_RETRIEVAL)
    adapter_used = mode in (TrialMode.ADAPTER, TrialMode.ADAPTER_RETRIEVAL)

    # Build prompt context string
    context_parts: list[str] = []
    if context_bundle.get("project_context"):
        proj = context_bundle["project_context"]
        projects = proj.get("projects") or []
        if projects:
            context_parts.append("Projects: " + ", ".join(p.get("label") or p.get("node_id") or "" for p in projects[:10]))
    style_ctx = context_bundle.get("style_context") or {}
    signals = style_ctx.get("style_signals") or []
    if signals:
        context_parts.append("Style signals: " + str(signals)[:500])
    if context_bundle.get("retrieved_text"):
        context_parts.append("Retrieved context:\n" + (context_bundle["retrieved_text"] or "")[:2000])
    context_str = "\n\n".join(context_parts) if context_parts else "No context provided."

    prompt = (trial.prompt_template or "Task: {task_goal}\n\nContext:\n{context}").format(
        context=context_str,
        task_goal=trial.task_goal,
    )

    model_response = ""
    evidence_used: list[str] = []

    if mode == TrialMode.BASELINE:
        model_response = f"[Baseline] Task: {trial.task_goal}. No model run; placeholder. Review context manually."
        evidence_used = list(context_bundle.keys())
    else:
        # Need LLM
        if not llm_config:
            model_response = "[No LLM config] Cannot run adapter or retrieval mode."
        else:
            if retrieval_used and corpus_path and Path(corpus_path).exists():
                from workflow_dataset.llm.retrieval_context import retrieve, format_context_for_prompt
                query = trial.task_goal or "workflow"
                docs = retrieve(corpus_path, query, top_k=retrieval_top_k)
                ctx = format_context_for_prompt(docs, max_chars=2000)
                if ctx:
                    prompt = "Context (retrieved):\n" + ctx + "\n\nUser: " + prompt
                    evidence_used.append("retrieved_docs")

            backend_name = llm_config.get("backend", "mlx")
            base_model = llm_config.get("base_model", "")
            if not base_model:
                model_response = "[No base_model in config]"
            else:
                from workflow_dataset.llm.train_backend import get_backend
                backend = get_backend(backend_name)
                max_tokens = int(llm_config.get("max_seq_length", 2048) // 4)
                try:
                    if adapter_used and adapter_path and Path(adapter_path).exists():
                        model_response = backend.run_inference(
                            base_model,
                            prompt,
                            max_tokens=max_tokens,
                            adapter_path=adapter_path,
                        )
                    else:
                        model_response = backend.run_inference(
                            base_model,
                            prompt,
                            max_tokens=max_tokens,
                        )
                    if not evidence_used and (context_bundle.get("project_context") or context_bundle.get("style_signals")):
                        evidence_used = ["context_bundle"]
                except Exception as e:
                    model_response = f"[inference error: {e}]"

    # Heuristic scoring
    scores = score_result(
        trial=trial,
        mode=mode,
        model_response=model_response,
        context_bundle=context_bundle,
        retrieval_used=retrieval_used,
    )

    result_id = stable_id("trial_result", trial.trial_id, mode.value, utc_now_iso(), prefix="res")
    status = "failed" if "[error]" in model_response.lower() or "[no " in model_response.lower() else "completed"
    if model_response and len(model_response.strip()) < 20:
        status = "partial"

    result = WorkflowTrialResult(
        result_id=result_id,
        trial_id=trial.trial_id,
        model_mode=mode.value,
        retrieval_used=retrieval_used,
        adapter_used=adapter_used,
        output_paths=[],
        model_response=(model_response or "")[:10000],
        evidence_used=evidence_used,
        task_completion_score=scores.get("task_completion", 0.0),
        style_match_score=scores.get("style_match", 0.0),
        retrieval_grounding_score=scores.get("retrieval_grounding", 0.0),
        bundle_usefulness_score=scores.get("bundle_usefulness", 0.0),
        safety_score=scores.get("safety", 1.0),
        adoption_ready=False,
        completion_status=status,
        notes="",
        created_utc=utc_now_iso(),
    )

    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        result_path = output_dir / f"{result_id}.json"
        with open(result_path, "w", encoding="utf-8") as f:
            f.write(result.model_dump_json(indent=2))

    return result


def run_trial_suite(
    trials: list[WorkflowTrial],
    modes: list[TrialMode],
    *,
    context_bundle: dict[str, Any],
    llm_config: dict[str, Any] | None = None,
    adapter_path: str | Path | None = None,
    corpus_path: str | Path | None = None,
    retrieval_top_k: int = 5,
    output_dir: Path | str | None = None,
) -> list[WorkflowTrialResult]:
    """Run multiple trials in multiple modes; return all results."""
    results: list[WorkflowTrialResult] = []
    for trial in trials:
        for mode in modes:
            res = run_trial(
                trial,
                mode,
                context_bundle=context_bundle,
                llm_config=llm_config,
                adapter_path=adapter_path,
                corpus_path=corpus_path,
                retrieval_top_k=retrieval_top_k,
                output_dir=output_dir,
            )
            results.append(res)
    return results

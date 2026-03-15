"""
M17: Heuristic scoring for workflow trial results. Explicitly heuristic; no fake ground truth.
"""

from __future__ import annotations

from typing import Any

from workflow_dataset.trials.trial_models import WorkflowTrial, TrialMode


def score_result(
    trial: WorkflowTrial,
    mode: TrialMode,
    model_response: str,
    context_bundle: dict[str, Any],
    retrieval_used: bool,
) -> dict[str, float]:
    """
    Return heuristic scores 0–1 for task_completion, style_match, retrieval_grounding, bundle_usefulness, safety.
    All scores are best-effort heuristics, not ground truth.
    """
    r = (model_response or "").strip().lower()
    scores: dict[str, float] = {
        "task_completion": 0.0,
        "style_match": 0.0,
        "retrieval_grounding": 0.0,
        "bundle_usefulness": 0.0,
        "safety": 1.0,
    }

    # Task completion: has substantive length and no error marker
    if "[error]" in r or "[inference error" in r or "[no llm" in r or "[no base_model" in r:
        scores["task_completion"] = 0.0
        scores["safety"] = 1.0
        return scores
    if len(r) < 30:
        scores["task_completion"] = 0.2
    elif len(r) < 100:
        scores["task_completion"] = 0.5
    else:
        scores["task_completion"] = 0.7
    if any(x in r for x in ("suggest", "recommend", "structure", "summary", "next step", "workflow", "project")):
        scores["task_completion"] = min(1.0, scores["task_completion"] + 0.2)

    # Style match: mentions user/style/pattern (heuristic)
    if any(x in r for x in ("user", "style", "pattern", "based on", "context")):
        scores["style_match"] = 0.5
    if any(x in r for x in ("user's style", "user's workflow", "prior pattern")):
        scores["style_match"] = 0.8

    # Retrieval grounding: if retrieval was used, did response look grounded?
    if retrieval_used:
        if len(r) > 80 and not r.startswith("[baseline]"):
            scores["retrieval_grounding"] = 0.6
        if any(x in r for x in ("based on the context", "from the", "occupation", "workflow", "task")):
            scores["retrieval_grounding"] = 0.8
    else:
        scores["retrieval_grounding"] = 0.5  # N/A

    # Bundle usefulness: would this be usable as a scaffold? (heuristic)
    if "structure" in r or "scaffold" in r or "bundle" in r or "1." in r or "2." in r or "- " in r:
        scores["bundle_usefulness"] = 0.6
    if "approval" in r or "without approval" in r or "do not execute" in r:
        scores["safety"] = 0.9

    return scores

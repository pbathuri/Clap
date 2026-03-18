"""
M41A: Pattern mapping from Karpathy (and other) reference repos to current product.
"""

from __future__ import annotations

from typing import Any

from workflow_dataset.learning_lab.models import (
    PatternMapping,
    ADOPT_DIRECT_CONCEPTUAL,
    ADOPT_PARTIAL,
    REJECT,
)


# Predefined mappings from inspection (no external code execution)
KARPATHY_PATTERN_MAPPINGS: list[PatternMapping] = [
    PatternMapping(
        reference_repo="karpathy/autoresearch",
        extracted_pattern="Experiment loop: modify → run (fixed budget) → compare metric → keep/discard",
        current_target_subsystem="learning_lab.experiments",
        adoption_type=ADOPT_PARTIAL,
        rationale="We adopt experiment-as-object and outcome (reject/quarantine/promote); no train.py or GPU.",
        local_first_compatible=True,
        production_cut_compatible=True,
        trust_review_implications="Outcomes still gated by council/safe_adaptation; lab only records.",
    ),
    PatternMapping(
        reference_repo="karpathy/autoresearch",
        extracted_pattern="Program/context document as human-editable agent instructions",
        current_target_subsystem="learning_lab.approved_scope",
        adoption_type=ADOPT_PARTIAL,
        rationale="Approved learning scope and experiment brief as optional context; no agent auto-run.",
        local_first_compatible=True,
        production_cut_compatible=True,
        trust_review_implications="Scope is metadata only; does not auto-apply.",
    ),
    PatternMapping(
        reference_repo="karpathy/nanochat",
        extracted_pattern="Single complexity dial; eval metrics and task-based eval structure",
        current_target_subsystem="eval.board, learning_lab.report",
        adoption_type=ADOPT_PARTIAL,
        rationale="Conceptual only; we use existing eval compare_runs and thresholds, no training code.",
        local_first_compatible=True,
        production_cut_compatible=True,
        trust_review_implications="None; read-only reference.",
    ),
    PatternMapping(
        reference_repo="karpathy/jobs",
        extracted_pattern="Score with rubric + rationale per item; dataset slice → LLM eval pipeline",
        current_target_subsystem="learning_lab.local_slice, safe_adaptation.evidence_bundle",
        adoption_type=ADOPT_PARTIAL,
        rationale="Local slice and evidence bundle with rationale; no OpenRouter or external API.",
        local_first_compatible=True,
        production_cut_compatible=True,
        trust_review_implications="Evidence stays local; no cloud scoring.",
    ),
    PatternMapping(
        reference_repo="karpathy/llm-council",
        extracted_pattern="Multi-LLM response → anonymized review/rank → Chairman synthesizes",
        current_target_subsystem="council.review, council.synthesis",
        adoption_type=ADOPT_DIRECT_CONCEPTUAL,
        rationale="Already implemented; council does multi-perspective review and synthesis.",
        local_first_compatible=True,
        production_cut_compatible=True,
        trust_review_implications="Existing council and presets.",
    ),
    PatternMapping(
        reference_repo="karpathy/nanochat",
        extracted_pattern="Full LLM training: tokenization, pretraining, finetuning, inference",
        current_target_subsystem="(none)",
        adoption_type=REJECT,
        rationale="Would require GPU and change product to training platform; not local-first.",
        local_first_compatible=False,
        production_cut_compatible=False,
        trust_review_implications="N/A rejected.",
    ),
    PatternMapping(
        reference_repo="karpathy/autoresearch",
        extracted_pattern="Agent edits train.py and runs 5-min GPU training",
        current_target_subsystem="(none)",
        adoption_type=REJECT,
        rationale="Self-modifying code and GPU; we only adopt experiment-outcome pattern.",
        local_first_compatible=False,
        production_cut_compatible=False,
        trust_review_implications="N/A rejected.",
    ),
    PatternMapping(
        reference_repo="karpathy/jobs",
        extracted_pattern="OpenRouter API, Playwright scrape, external BLS data",
        current_target_subsystem="(none)",
        adoption_type=REJECT,
        rationale="Cloud and external API; we adopt only rubric+rationale concept locally.",
        local_first_compatible=False,
        production_cut_compatible=False,
        trust_review_implications="N/A rejected.",
    ),
]


def build_pattern_mapping_report(
    include_rejected: bool = True,
) -> dict[str, Any]:
    """Build pattern mapping report for CLI and mission control."""
    adopted = [p for p in KARPATHY_PATTERN_MAPPINGS if p.adoption_type != REJECT]
    rejected = [p for p in KARPATHY_PATTERN_MAPPINGS if p.adoption_type == REJECT]
    direct = [p for p in KARPATHY_PATTERN_MAPPINGS if p.adoption_type == ADOPT_DIRECT_CONCEPTUAL]
    partial = [p for p in KARPATHY_PATTERN_MAPPINGS if p.adoption_type == ADOPT_PARTIAL]
    return {
        "mappings": [p.to_dict() for p in (KARPATHY_PATTERN_MAPPINGS if include_rejected else adopted)],
        "adopted_count": len(adopted),
        "rejected_count": len(rejected),
        "direct_fit_count": len(direct),
        "partial_fit_count": len(partial),
        "reference_repos": list({p.reference_repo for p in KARPATHY_PATTERN_MAPPINGS}),
        "in_use_note": "Patterns applied conceptually; no external code or cloud.",
    }

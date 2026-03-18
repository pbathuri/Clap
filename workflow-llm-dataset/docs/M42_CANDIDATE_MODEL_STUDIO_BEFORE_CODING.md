# M42E–M42H — Candidate Model Studio: Before-Coding Analysis

## 1. What experiment/adaptation/training-like pieces already exist

- **safe_adaptation**: `AdaptationCandidate`, `AdaptationEvidenceBundle`, boundary check, quarantine, review decision; persisted under `data/local/safe_adaptation/candidates/`; evidence from triage + corrections; `create_candidate()` builds evidence bundle from cohort evidence and correction_ids.
- **personal_adaptation**: `PreferenceCandidate` with evidence, source (corrections | routines | style_profile | teaching), review_status; `generate_preference_candidates()` from corrections.
- **council**: Multi-perspective evaluation, `CouncilReview`, synthesis (promote / quarantine / reject / limited / needs_evidence / safe_experimental_only), presets, promotion policy; `run_council_review(subject_id, subject_type, ...)`; persisted reviews.
- **corrections**: `CorrectionEvent` store; `list_corrections(..., eligible_only)`; categories and source types; no direct link to “model” except via adaptation candidates.
- **triage**: `UserObservedIssue`, `IssueCluster` (by subsystem/workflow); `build_clusters_by_subsystem`, `build_clusters_by_workflow`; evidence store; health summary.
- **incubator**: Workflow candidates (idea → prototype → benchmarked → cohort_tested → promoted/rejected); `list_candidates`, `add_candidate`, `attach_evidence`; generic dict store under `data/local/incubator`.
- **devlab**: Experiments queue, proposals, model_lab; experiment/proposal lifecycle—distinct from “candidate model” (workflow/feature candidates, not model-weight candidates).
- **teaching**: Skills, scorecard, review, normalize—teaching signals for style/routine, not model training.
- **production_cut / release / reliability / vertical_selection / trust / policy**: Define what is supported vs experimental, freeze, rollout—constrain where candidate models may apply; no training logic.
- **eval**: `eval/board`, `list_runs`, benchmark runs—evaluation only; no candidate model type yet.
- **assist_engine**: Suggestion models (AssistSuggestion, etc.)—runtime behavior models, not “candidate model” experiments.

So: **adaptation candidates + evidence bundles + council + corrections + issue clusters + incubator + eval** are the main building blocks. There is no explicit “candidate model” (model variant / distillation path) or “dataset slice” type yet.

---

## 2. Which useful repo patterns fit candidate-model creation

- **Evidence → candidate**: Reuse pattern from `safe_adaptation`: evidence bundle (evidence_ids, correction_ids, session_ids) backing a single candidate; same idea for “candidate model” backed by a dataset slice with provenance.
- **Boundary / supported vs experimental**: Reuse `safe_adaptation` surface_type and production_cut notions so candidate models are clearly supported vs experimental; no silent promotion to supported.
- **Council review before promotion**: Reuse council for “promote candidate model” decisions; subject_type can include `candidate_model`.
- **Quarantine / rollback**: Reuse quarantine and review decision pattern; candidate models can be quarantined and have explicit rollback path.
- **Store pattern**: File-based, one JSON per candidate under a dedicated dir (like safe_adaptation/candidates, incubator); lineage in same store or sidecar.
- **Incubator-style stages**: Idea → prototype → benchmarked → cohort_tested → promoted fits “candidate model” lifecycle; we add dataset_slice_id, training_path_id, runtime_variant.
- **Eval board**: Existing eval runs can be referenced as “required evaluation before promotion” for a candidate model; no need to replace eval.

From Karpathy-style repos (conceptual only; no code copy):
- **nanochat**: Small, local-first training/eval loop—inspiration for “local path” and “expected compute”; we only define path types and contracts, not implement training.
- **llm-council**: Multi-model evaluation—aligns with council + multi-perspective; we already have council; we add candidate_model as a reviewable subject.
- **jobs**: Job configs and runner—we have ops_jobs; candidate-model “training” could be a job type later; first draft we only define path metadata.

---

## 3. Which do not fit and why

- **Full training implementation**: We are not building a cloud training platform or implementing backward pass / optimizer; we define “training path” as a contract (scope, compute, risks, required eval).
- **Uncontrolled continual learning**: Any training path is explicit, bounded by dataset slice and path type; no “train on everything” or silent ingestion.
- **Replacing adaptation/council/incubator**: We are not rewriting safe_adaptation or council; we add a new “candidate model” concept that can reference adaptations, council reviews, and incubator patterns.
- **Karpathy code copy**: We do not copy nanochat/autoresearch/jobs code; we use at most patterns (local store, eval gate, job-like descriptor).

---

## 4. Exact file plan

| Area | Path | Purpose |
|------|------|--------|
| Doc | `docs/M42_CANDIDATE_MODEL_STUDIO_BEFORE_CODING.md` | This file. |
| Models | `src/workflow_dataset/candidate_model_studio/models.py` | CandidateModel, CandidateRuntimeVariant, TrainingDistillationPath, DatasetSlice, EvidenceBundle (studio), ExperimentLineage, PromotionEligibility, RollbackPath, SupportedExperimentalBoundary. |
| Slice curation | `src/workflow_dataset/candidate_model_studio/dataset_slice.py` | Build bounded slices from corrections, accepted adaptations, issue clusters, vertical failures, review-studio artifacts, council disagreement cases, production-safe exemplars; provenance + exclusion rules. |
| Paths | `src/workflow_dataset/candidate_model_studio/training_paths.py` | Path type definitions: prompt_config_only, routing_only, lightweight_distillation, critique_evaluator, vertical_specialist; each: allowed_scope, compute_assumptions, risks, required_evaluation_before_promotion. |
| Store | `src/workflow_dataset/candidate_model_studio/store.py` | Persist/list candidate models, slices, lineage; `data/local/candidate_model_studio/`. |
| Create | `src/workflow_dataset/candidate_model_studio/create.py` | Create candidate from evidence source (e.g. issue_cluster_123, adaptation_id, correction_set). |
| Reports | `src/workflow_dataset/candidate_model_studio/report.py` | Report for one candidate (id); lineage summary. |
| CLI | `src/workflow_dataset/cli.py` | Add `model_studio_group`; commands: candidates, create, dataset, lineage, report. |
| Mission control | `src/workflow_dataset/mission_control/state.py` | Add `candidate_model_studio_state`: top candidate, latest slice, risky/quarantined, lineage summary, next required evaluation step. |
| Tests | `tests/test_candidate_model_studio.py` | Candidate creation, dataset slice curation, lineage, allowed/disallowed path behavior, quarantined handling, no-evidence/weak-dataset. |
| Doc | `docs/M42_CANDIDATE_MODEL_STUDIO.md` | User-facing: CLI usage, sample record, sample slice/lineage, sample report, gaps. |

---

## 5. Safety/risk note

- **No silent production mutation**: Promotion to “supported” requires explicit council review (or equivalent gating); candidate model studio only records eligibility and rollback path.
- **Bounded data**: Dataset slices are explicit and provenance-tracked; exclusion rules prevent “sweep everything” into a slice.
- **Quarantine**: Risky or low-evidence candidates are quarantined; visible in mission control; no auto-promotion.
- **Rollback path**: Every candidate model record can point to a rollback target (e.g. previous runtime or baseline); reversal is explicit.

---

## 6. Candidate-model principles

- Evidence-first: candidate models are created from real product evidence (corrections, adaptations, issue clusters, etc.), not from unbounded corpora.
- Bounded slices: each experiment uses a curated dataset slice with provenance and exclusion rules.
- Explicit paths: training/distillation is one of the defined path types with scope, compute, risks, and required evaluation.
- Reviewable: all candidates and lineage are inspectable; promotion requires evaluation and (optionally) council.
- Reversible: rollback path is stored; supported/experimental boundary is explicit.

---

## 7. What this block will NOT do

- Implement actual training or distillation code (backward pass, optimizers, checkpoints).
- Build a cloud finetuning or training platform.
- Allow production model mutation without explicit review.
- Replace or duplicate learning-lab, adaptation, council, release, reliability, trust, policy systems.
- Silently add all data into slices; every slice has explicit provenance and exclusion rules.
- Introduce uncontrolled continual learning or model drift.

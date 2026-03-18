# M42E–M42H — Candidate Model Studio

Local candidate-model studio: create bounded experiments from evidence, curate dataset slices, track lineage, and produce reviewable candidate runtimes. No uncontrolled continual learning; no production mutation without explicit review.

---

## 1. Files modified

- `src/workflow_dataset/cli.py` — Added `model-studio` Typer group and commands: `candidates`, `create`, `dataset`, `lineage`, `report`.
- `src/workflow_dataset/mission_control/state.py` — Added `candidate_model_studio_state` to mission control (top candidate, latest slice, quarantined, next eval step).

## 2. Files created

- `docs/M42_CANDIDATE_MODEL_STUDIO_BEFORE_CODING.md` — Before-coding analysis (existing pieces, patterns, file plan, safety, principles).
- `src/workflow_dataset/candidate_model_studio/__init__.py` — Package exports.
- `src/workflow_dataset/candidate_model_studio/models.py` — CandidateModel, CandidateRuntimeVariant, TrainingDistillationPath, DatasetSlice, StudioEvidenceBundle, ExperimentLineage, PromotionEligibility, RollbackPath, SupportedExperimentalBoundary.
- `src/workflow_dataset/candidate_model_studio/dataset_slice.py` — Slice builders: corrections, accepted_adaptations, issue_cluster, vertical_failures, council_disagreement, production_safe; provenance and exclusion.
- `src/workflow_dataset/candidate_model_studio/training_paths.py` — Path types: prompt_config_only, routing_only, lightweight_distillation, critique_evaluator, vertical_specialist; each with scope, compute, risks, required evaluation.
- `src/workflow_dataset/candidate_model_studio/store.py` — Persist/load candidates and slices under `data/local/candidate_model_studio/`.
- `src/workflow_dataset/candidate_model_studio/create.py` — create_candidate(from_source=...), create from issue_cluster, adaptation, correction_set.
- `src/workflow_dataset/candidate_model_studio/report.py` — build_lineage_summary, build_candidate_report, get_mission_control_candidate_studio_state.
- `tests/test_candidate_model_studio.py` — Tests for creation, slice curation, lineage, path descriptors, quarantined, no-evidence/weak-dataset, full report.
- `docs/M42_CANDIDATE_MODEL_STUDIO.md` — This file.

---

## 3. Exact CLI usage

```bash
# List candidate models
workflow-dataset model-studio candidates [--repo-root PATH] [--status draft|ready_for_eval|quarantined|promoted|rejected] [--cohort ID] [--limit N] [--json]

# Create from issue cluster (cluster_xxx or issue_cluster_xxx)
workflow-dataset model-studio create --from issue_cluster_123 [--cohort COHORT] [--name NAME] [--path prompt_config_only|routing_only|lightweight_distillation|critique_evaluator|vertical_specialist] [--repo-root PATH] [--json]

# Create from adaptation
workflow-dataset model-studio create --from adaptation_adapt_abc123 [--cohort COHORT] [--name NAME] [--path prompt_config_only] [--repo-root PATH]

# Create from correction set
workflow-dataset model-studio create --from "correction_set:corr_1,corr_2,corr_3" [--cohort COHORT] [--name NAME] [--repo-root PATH]

# Show dataset slice(s) for a candidate
workflow-dataset model-studio dataset --id cand_xxx [--repo-root PATH] [--json]

# Show lineage for a candidate
workflow-dataset model-studio lineage --id cand_xxx [--repo-root PATH] [--json]

# Full report for a candidate
workflow-dataset model-studio report --id cand_xxx [--repo-root PATH] [--json]
```

---

## 4. Sample candidate model record

```json
{
  "candidate_id": "cand_a1b2c3d4e5f6",
  "name": "Candidate from cluster_executor_xyz",
  "summary": "From issue cluster cluster_executor_xyz; slice row_count=12",
  "status": "draft",
  "evidence": {
    "evidence_ids": [],
    "correction_ids": [],
    "adaptation_ids": [],
    "cluster_ids": ["cluster_executor_xyz"],
    "session_ids": [],
    "summary": "1 clusters",
    "evidence_count": 1
  },
  "dataset_slice_id": "slice_abc123",
  "training_path_id": "prompt_config_only",
  "runtime_variant_id": "",
  "cohort_id": "careful_first_user",
  "lineage": {
    "candidate_id": "cand_a1b2c3d4e5f6",
    "parent_candidate_ids": [],
    "evidence_source_type": "issue_cluster",
    "evidence_source_id": "cluster_executor_xyz",
    "created_at_utc": "2025-03-16T12:00:00Z",
    "created_by": "cli"
  },
  "boundary": {
    "candidate_id": "cand_a1b2c3d4e5f6",
    "boundary": "experimental",
    "summary": "Created from issue cluster; experimental until promoted"
  },
  "created_at_utc": "2025-03-16T12:00:00Z",
  "updated_at_utc": "2025-03-16T12:00:00Z"
}
```

---

## 5. Sample dataset slice / lineage output

**Dataset (model-studio dataset --id cand_xxx):**

```json
{
  "candidate_id": "cand_xxx",
  "dataset_slice_id": "slice_abc123",
  "slices": [
    {
      "slice_id": "slice_abc123",
      "candidate_id": "cand_xxx",
      "name": "Cluster cluster_executor_xyz",
      "provenance_source": "issue_clusters",
      "provenance_refs": ["cluster_executor_xyz"],
      "included_evidence_ids": ["ev_1", "ev_2"],
      "included_correction_ids": [],
      "exclusion_rule_summary": "",
      "excluded_ids": [],
      "created_at_utc": "2025-03-16T12:00:00Z",
      "row_count": 12
    }
  ]
}
```

**Lineage (model-studio lineage --id cand_xxx):**

```json
{
  "candidate_id": "cand_xxx",
  "found": true,
  "name": "Candidate from cluster_executor_xyz",
  "status": "draft",
  "created_at_utc": "2025-03-16T12:00:00Z",
  "evidence_source_type": "issue_cluster",
  "evidence_source_id": "cluster_executor_xyz",
  "parent_candidate_ids": []
}
```

---

## 6. Sample candidate report

**model-studio report --id cand_xxx (--json):**

```json
{
  "candidate_id": "cand_xxx",
  "found": true,
  "name": "Candidate from cluster_executor_xyz",
  "summary": "From issue cluster cluster_executor_xyz; slice row_count=12",
  "status": "draft",
  "evidence_count": 1,
  "dataset_slice_id": "slice_abc123",
  "slices": [...],
  "training_path_id": "prompt_config_only",
  "training_path": {
    "path_id": "prompt_config_only",
    "label": "Prompt / config only",
    "allowed_scope": "Prompt text, system config, or inference params only. No weight changes.",
    "compute_assumptions": "Local; no GPU required. Edit config/prompt and re-run eval.",
    "risks": ["Prompt injection sensitivity", "Drift if prompts change without review"],
    "required_evaluation_before_promotion": ["Eval run on supported workflows", "Regression check vs baseline"]
  },
  "lineage": { "evidence_source_type": "issue_cluster", "evidence_source_id": "cluster_executor_xyz", ... },
  "promotion_eligibility": null,
  "rollback_path": null,
  "boundary": { "boundary": "experimental", ... },
  "created_at_utc": "2025-03-16T12:00:00Z",
  "updated_at_utc": "2025-03-16T12:00:00Z"
}
```

---

## 7. Exact tests run

```bash
cd workflow-llm-dataset
pytest tests/test_candidate_model_studio.py -v
```

Tests cover:

- **test_candidate_model_creation** — Create and persist candidate; load and list.
- **test_dataset_slice_curation** — Build slice from corrections with provenance and exclusion; save/load slice.
- **test_lineage_provenance** — Lineage summary reflects source type and id.
- **test_training_path_descriptor** — Path descriptors have allowed_scope, risks, required_evaluation_before_promotion.
- **test_quarantined_candidate** — Quarantined candidate listable and in mission control state.
- **test_no_evidence_weak_dataset** — Candidate with empty evidence; slice with row_count 0; report still valid.
- **test_candidate_report_full** — Full report includes training_path, lineage, boundary.

---

## 8. Remaining gaps for later refinement

- **Create from vertical_failures / production_safe** — Slice builders exist; no CLI shorthand yet (e.g. `--from vertical_failures:subsystem_xyz`).
- **Council review integration** — subject_type `candidate_model` can be wired in council review; not yet in council presets.
- **Promotion eligibility computation** — PromotionEligibility is stored but not auto-computed from eval runs + council.
- **Rollback path persistence** — RollbackPath is on model; no dedicated “set rollback” CLI or workflow.
- **Runtime variant emission** — CandidateRuntimeVariant and runtime_variant_id are modeled; no actual emission of config/routing/checkpoint ref yet.
- **Eval run linking** — Link candidate to eval run IDs for “required_evals_done”; requires eval store integration.
- **Quarantine from studio** — Quarantine is status; no dedicated model-studio quarantine command (could call safe_adaptation or add studio-specific quarantine).
- **Path-specific execution** — Training paths are descriptors only; no runner that executes prompt_config_only or lightweight_distillation steps.

These are left as follow-up work so the first draft stays coherent and scoped.

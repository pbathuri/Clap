# M41A–M41D Local Learning Lab — Deliverable

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/cli.py` | Added `learning-lab` group and commands: patterns, experiments, create, compare, report, outcome. |
| `src/workflow_dataset/mission_control/state.py` | Added `learning_lab_state` (active_experiment_id, top_active_experiment, recent_promoted/rejected, pattern_mappings_in_use_count, quarantined_experiments_count, next_improvement_review). |
| `src/workflow_dataset/mission_control/report.py` | Added report block for Learning lab. |

## 2. Files created

| File | Purpose |
|------|--------|
| `src/workflow_dataset/learning_lab/__init__.py` | Public API. |
| `src/workflow_dataset/learning_lab/models.py` | PatternMapping, ImprovementExperiment, LocalLearningSlice, ExperimentEvidenceBundle, RollbackableChangeSet, ApprovedLearningScope; adoption/outcome/source constants. |
| `src/workflow_dataset/learning_lab/pattern_mapping.py` | KARPATHY_PATTERN_MAPPINGS, build_pattern_mapping_report. |
| `src/workflow_dataset/learning_lab/store.py` | save_experiment, list_experiments, get_experiment, set/get active_experiment_id; data/local/learning_lab/experiments.jsonl. |
| `src/workflow_dataset/learning_lab/experiments.py` | create_experiment_from_issue_cluster, from_repeated_correction, from_accepted_adaptation; compare_before_after; record_outcome. |
| `src/workflow_dataset/learning_lab/report.py` | build_experiment_report, build_comparison_output. |
| `tests/test_learning_lab.py` | 14 tests: pattern mapping, experiment model, save/list/get, compare, record outcome, report, create (no cluster / insufficient), active id. |
| `docs/M41A_M41D_LEARNING_LAB_BEFORE_CODING.md` | Before-coding: what exists, Karpathy inspection, adopt/reject, file plan, safety. |
| `docs/M41A_M41D_LEARNING_LAB_DELIVERABLE.md` | This file. |

---

## 3. Exact mapping from each Karpathy repo to adopted/rejected ideas

| Repo | Adopted (conceptual) | Rejected |
|------|----------------------|----------|
| **karpathy/autoresearch** | Experiment loop (modify → run → compare → keep/discard); experiment-as-object; outcome reject/quarantine/promote. Program/context as optional approved scope. | Agent editing train.py; 5-min GPU training; self-modifying code. |
| **karpathy/nanochat** | Single complexity dial; eval metrics and task structure as reference. Compare before/after on slice. | Full training/finetuning/inference code; GPU; CORE/training. |
| **karpathy/jobs** | Score-with-rubric + rationale; dataset slice → eval concept. Local slice + evidence bundle. | OpenRouter API; Playwright scrape; BLS/jobs domain. |
| **karpathy/llm-council** | Multi-perspective then synthesize — already implemented in council.review/synthesis. Document as direct conceptual fit. | FastAPI + React + OpenRouter app. |

---

## 4. Sample pattern-mapping report

**CLI:** `workflow-dataset learning-lab patterns`

```
Pattern mappings  adopted=5  rejected=3
  Patterns applied conceptually; no external code or cloud.
  karpathy/autoresearch  partial_fit  Experiment loop: modify → run (fixed budget) → compare metric → keep/discard
  karpathy/autoresearch  partial_fit  Program/context document as human-editable agent instructions
  karpathy/nanochat  partial_fit  Single complexity dial; eval metrics and task-based eval structure
  karpathy/jobs  partial_fit  Score with rubric + rationale per item; dataset slice → LLM eval pipeline
  karpathy/llm-council  direct_conceptual_fit  Multi-LLM response → anonymized review/rank → Chairman synthesizes
  ...
```

**JSON excerpt:** `learning-lab patterns --json`

```json
{
  "adopted_count": 5,
  "rejected_count": 3,
  "direct_fit_count": 1,
  "partial_fit_count": 4,
  "reference_repos": ["karpathy/autoresearch", "karpathy/nanochat", "karpathy/jobs", "karpathy/llm-council"],
  "in_use_note": "Patterns applied conceptually; no external code or cloud.",
  "mappings": [
    {
      "reference_repo": "karpathy/autoresearch",
      "extracted_pattern": "Experiment loop: modify → run (fixed budget) → compare metric → keep/discard",
      "current_target_subsystem": "learning_lab.experiments",
      "adoption_type": "partial_fit",
      "rationale": "We adopt experiment-as-object and outcome (reject/quarantine/promote); no train.py or GPU.",
      "local_first_compatible": true,
      "production_cut_compatible": true
    }
  ]
}
```

---

## 5. Sample improvement experiment

After creating from an issue cluster (when clusters exist):

```json
{
  "experiment_id": "exp_abc123...",
  "source_type": "issue_cluster",
  "source_ref": "cluster_subsystem_xyz",
  "label": "Experiment from cluster cluster_subsystem_xyz",
  "created_at_utc": "2026-03-17T20:00:00Z",
  "status": "pending",
  "status_reason": "",
  "local_slice": {
    "slice_id": "slice_...",
    "description": "Issue cluster cluster_subsystem_xyz: 3 issues",
    "issue_ids": ["issue_1", "issue_2", "issue_3"],
    "evidence_ids": ["ev_1", "ev_2"]
  },
  "evidence_bundle": {
    "evidence_ids": ["ev_1", "ev_2"],
    "correction_ids": [],
    "session_ids": [],
    "summary": "Cluster cluster_subsystem_xyz; 3 issues"
  },
  "comparison_summary": "",
  "rollbackable_changes": [],
  "approved_scope_id": ""
}
```

---

## 6. Sample comparison/evidence output

**Compare (no runs):** `workflow-dataset learning-lab compare --id exp_abc123`

```
Comparison  exp_abc123
  3 issues; 2 evidence; Cluster ...; 3 issues
```

**Report:** `workflow-dataset learning-lab report --id exp_abc123`

```
Experiment from cluster cluster_subsystem_xyz  exp_abc123
  source=issue_cluster  ref=cluster_subsystem_xyz  status=pending
  3 issues; 2 evidence; Cluster ...
  evidence: Cluster cluster_subsystem_xyz; 3 issues
```

**Record outcome:** `workflow-dataset learning-lab outcome --id exp_abc123 --outcome promoted --reason "Evidence strong"`

```
Recorded  exp_abc123  outcome=promoted
```

---

## 7. Exact tests run

```bash
pytest tests/test_learning_lab.py -v --tb=short
```

**Result:** 14 passed (0.06s).

- test_pattern_mapping_report  
- test_pattern_mapping_adopted_only  
- test_experiment_model_to_dict  
- test_save_and_list_experiments  
- test_get_experiment  
- test_compare_before_after_no_runs  
- test_compare_nonexistent  
- test_record_outcome  
- test_record_outcome_invalid  
- test_build_experiment_report  
- test_build_experiment_report_not_found  
- test_create_from_issue_cluster_no_cluster  
- test_create_from_repeated_correction_insufficient  
- test_active_experiment_id  

---

## 8. Exact remaining gaps for later refinement

- **Create from issue cluster:** Depends on triage clusters existing; when no clusters, create returns None. Optional: create a “synthetic” experiment from a single issue or manual slice.
- **Create from repeated correction:** Requires propose_updates to return at least one proposed update for the given target with enough correction_ids; otherwise returns None. Optional: lower min_corrections or support “single correction” experiment.
- **Create from accepted_adaptation:** Loads candidate and uses its evidence; if candidate file missing, evidence is empty but experiment still created. Optional: require candidate to exist and have non-empty evidence.
- **Before/after with eval runs:** compare_before_after(run_before, run_after) delegates to eval.board.compare_runs; optional: wire learning-lab compare to accept run aliases (e.g. latest, previous).
- **Approved learning scope:** Model exists but no store or CLI for defining/loading scope; optional: persist approved_scope and filter experiments by scope.
- **Quarantined “learning ideas”:** Mission control shows quarantined_experiments_count; no separate “quarantined pattern” or “rejected idea” list. Optional: separate table for rejected pattern ideas with reason.
- **Rollbackable change set:** Field on experiment is populated by future apply flows; currently empty. Optional: when applying correction/adaptation from an experiment, append to rollbackable_changes.

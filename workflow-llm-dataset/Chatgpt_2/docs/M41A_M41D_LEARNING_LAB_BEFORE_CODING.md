# M41A–M41D Local Learning Lab — Before Coding

## 1. What already exists in the current repo for learning/evaluation/improvement

- **Corrections (M23M):** `corrections/` — capture operator corrections (add_correction), propose_updates from learning rules, apply_update/revert_update, advisory_review_for_corrections. Data: `data/local/corrections/`. Mission control: proposed/applied/reverted counts, review_recommended.
- **Safe adaptation (M38I–M38L):** `safe_adaptation/` — candidates from triage/corrections, evidence_bundle (evidence_ids + correction_ids + session_ids), boundary check (supported/experimental/blocked), accept/reject/quarantine, apply_within_boundaries. Council runs on adaptation subjects with policy (promote/quarantine/reject).
- **Council (M41E–M41H):** `council/` — run_council_review(subject_id, subject_type), synthesize_decision (promote/quarantine/reject/limited/experimental_only), presets, promotion_policy. Persisted reviews; mission control: council state.
- **Eval / benchmark board:** `eval/` — list_runs, get_run, compare_runs(run_a, run_b), reconcile_run, check_run_against_thresholds; recommendation promote/hold/refine/revert. Runs dir with run_manifest.json per run.
- **Triage:** `triage/` — list_issues, build_clusters_by_subsystem, build_clusters_by_workflow, IssueCluster (cluster_id, issue_ids, severity, playbook_id). Evidence and health for cohort.
- **Teaching:** `teaching/` — correction_to_skill_draft, skill_store, skills from corrections; teaching report and review.
- **Candidate model studio:** `candidate_model_studio/` — create_candidate_from_corrections, create_candidate_from_adaptation; training paths, dataset_slice.
- **Personal adaptation:** `personal_adaptation/` — preference candidates from corrections, apply_accepted_preference.
- **Observe:** `observe/` — events, sources, profiles, manual_teaching; no explicit “learning lab” aggregation.

**Gap:** No single “improvement experiment” abstraction that ties: source (issue cluster / repeated correction / accepted adaptation) → local eval slice → before/after comparison → reject/quarantine/promote with evidence bundle. No explicit “reference pattern mapping” from external repos or “approved learning scope.”

---

## 2. What each Karpathy repo contributes (after inspection)

- **nanochat:** Full LLM training harness (tokenization, pretraining, finetuning, eval, inference, chat UI). Single complexity dial (depth); CORE metric; task-based evals (tasks/); report utilities. **Contribution:** Conceptual — minimal baseline, single dial, eval metrics and task structure; run comparison and leaderboard mindset. No code vendoring (GPU/training).
- **autoresearch:** AI agent edits `train.py`, runs fixed 5-min training, keeps/discards by val_bpb. `program.md` = human-editable agent instructions. **Contribution:** Experiment loop pattern — modify → run → compare metric → keep/discard; fixed time budget for comparability; single-file scope; program-as-context for the “research org.” No code vendoring (NN training).
- **jobs:** BLS scraper/parser, LLM scoring pipeline (score.py + rubric → scores.json with rationales). **Contribution:** Score-with-rubric + rationale per item; dataset slice → LLM eval pipeline concept. No OpenRouter or jobs domain code.
- **llm-council:** Multi-LLM query → each answers → anonymized review/rank → Chairman compiles. **Contribution:** Already aligned — our council does multi-perspective review and synthesis (promote/quarantine/reject). No code import; document alignment only.

---

## 3. Which ideas are safe to import conceptually

- **From autoresearch:** Experiment as first-class object with source (e.g. issue_cluster, repeated_correction, accepted_adaptation), run/comparison step, outcome (reject/quarantine/promote). Fixed or bounded “eval budget” (e.g. local slice size) for comparability. Program/context document as optional “approved learning scope” or experiment brief.
- **From nanochat:** Eval metric and task structure as reference only; “compare before/after on a slice” without importing training. Report utilities style: small, explicit report payloads.
- **From jobs:** Score-with-rubric + rationale stored per item in evidence bundle; “local eval slice” as explicit dataset slice id or filter.
- **From llm-council:** No new import; our council already provides multi-perspective synthesis; learning lab can feed adaptation/correction clusters into council and record outcome.

---

## 4. Which ideas should be rejected and why

- **nanochat training/finetuning/inference code:** Would require GPU, large deps, and change product to an LLM training platform. Reject.
- **autoresearch train.py editing and 5-min GPU training:** Self-modifying code and GPU; reject. We only adopt the *experiment loop* and outcome (keep/discard) pattern, applied to our existing eval/corrections/adaptation flows.
- **jobs OpenRouter/API and scraping:** Cloud and external API; reject. We only adopt rubric + rationale and slice-based eval concept locally.
- **llm-council app (FastAPI + React + OpenRouter):** Full stack and cloud; reject. We keep our existing council and mission control.

---

## 5. Exact file plan

| Path | Purpose |
|------|--------|
| `src/workflow_dataset/learning_lab/__init__.py` | Public API. |
| `src/workflow_dataset/learning_lab/models.py` | PatternMapping, ImprovementExperiment, LocalLearningSlice, ExperimentStatus, EvidenceBundle (ref), RollbackableChangeSet, ApprovedLearningScope; adoption_type enum. |
| `src/workflow_dataset/learning_lab/pattern_mapping.py` | Reference repo registry (Karpathy), extracted patterns, current-repo target, adoption_type, rationale; build_pattern_mapping_report. |
| `src/workflow_dataset/learning_lab/store.py` | Persist experiments, pattern mappings in use; `data/local/learning_lab/`. |
| `src/workflow_dataset/learning_lab/experiments.py` | create_experiment_from_issue_cluster, from_repeated_correction, from_accepted_adaptation; compare_before_after (delegate to eval/corrections); record_outcome (reject/quarantine/promote). |
| `src/workflow_dataset/learning_lab/report.py` | build_experiment_report(exp_id); build_comparison_output(exp_id). |
| CLI in `cli.py` | `learning-lab patterns`, `learning-lab experiments`, `learning-lab create --from issue_cluster|repeated_correction|accepted_adaptation`, `learning-lab compare --id`, `learning-lab report --id`. Additive. |
| `mission_control/state.py` | `learning_lab_state`: top active experiment, recent accepted/rejected, pattern mappings in use, quarantined count, next_improvement_review. |
| `mission_control/report.py` | Report block for learning lab. |
| `tests/test_learning_lab.py` | Pattern mapping, experiment creation, compare, evidence bundle, reject/quarantine/promote, no-experiment case. |
| `docs/M41A_M41D_LEARNING_LAB_DELIVERABLE.md` | Deliverable: mapping table, sample experiment, sample comparison, tests, gaps. |

---

## 6. Safety/risk note

- All experiments and pattern mappings are local, inspectable, and reversible. No cloud calls from learning lab; no hidden self-modification of core code.
- “Approved learning scope” and “quarantined learning ideas” are metadata only; they do not auto-apply changes. Promotion still goes through existing council/safe_adaptation/corrections flows.
- Pattern mapping is documentation and report only; it does not execute code from external repos.

---

## 7. What this block will NOT do

- Vendor nanochat, autoresearch, jobs, or llm-council code. No GPU training, no OpenRouter, no FastAPI/React app.
- Replace or rewrite corrections, safe_adaptation, council, or eval. Learning lab orchestrates and records; it does not duplicate their logic.
- Add cloud training or inference. No hidden continual learning.
- Auto-apply improvements without operator/council approval.

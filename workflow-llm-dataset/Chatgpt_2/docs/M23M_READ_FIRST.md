# M23M — Operator Correction Loop + Explicit Learning Updates — Read First

## 1. What already exists for recommendations, plans, jobs, trust, and specialization memory

- **Recommendations (M23K/M23L):** `recommend_jobs(repo_root, limit, context_snapshot)` returns list with `recommendation_id`, `job_pack_id`, `reason`, `mode_allowed`, `blocking_issues`, `why_now_evidence`, `context_trigger`. No capture of “operator rejected this” or “wrong timing.”
- **Plans:** `PlanPreview` (plan_id, job_pack_ids, mode, blocked, blocked_reasons); `build_plan_for_job` / `build_plan_for_routine`. No correction record when operator says “plan preview was wrong.”
- **Job runs:** `run_job`, `run_plan`; plan run record in `copilot/runs/<run_id>/plan_run.json` (executed, blocked, timestamp). Specialization can be updated via `update_from_successful_run` (explicit). No “operator corrected this run’s outcome” record.
- **Trust / approval:** `check_job_policy(job, mode, params, repo_root)`; approval_registry (approved_paths, approved_action_scopes). Trust level lives on JobPack (trust_level, trust_notes). No path for corrections to change trust; policy is enforced, not learned from freeform feedback.
- **Specialization memory (M23J):** `SpecializationMemory`: preferred_params, preferred_paths, preferred_apps, preferred_output_style, operator_notes, last_successful_run, recurring_failure_notes, update_history (at, source, summary). Update paths: `update_from_successful_run`, `update_from_operator_override`, `save_as_preferred`. Source is one of successful_run | operator_override | save_as_preferred. **This is the main store that can absorb operator feedback** (params, paths, notes, output_style) via existing `update_from_operator_override` and `save_as_preferred`; today there is no structured “correction event” that feeds them.
- **Context/triggers (M23L):** Trigger types (previous_job_succeeded, approval_present, reminder_due, etc.). No “trigger was false positive/negative” correction type or tuning.

## 2. What existing state can already absorb explicit operator feedback

- **Specialization:** `update_from_operator_override(job_pack_id, preferred_params=..., preferred_paths=..., operator_notes=...)` and `save_as_preferred(job_pack_id, params)` already persist to specialization.yaml and append to update_history. So “bad job parameter default” and “bad path preference” can be applied by calling these with correction-derived values; we need a **correction event** that records the operator’s intent and a **learning rule** that maps correction → proposed specialization update.
- **Job pack metadata:** JobPack is loaded from YAML; trust_level, trust_notes are in the file. We could allow “trust level too high/low” or “trust notes” as **advisory** correction that proposes a trust_notes update (not automatic privilege escalation). Changes to job pack YAML would be explicit writes (e.g. from an “apply-update” path that only updates trust_notes or similar safe fields).
- **Routine ordering:** Routines are YAML; `get_ordered_job_ids` uses ordering or job_pack_ids. A “routine ordering correction” could propose a new ordering and be applied by re-saving the routine.
- **Recommendation suppressions / preference hints:** No existing store. Would need a small local store (e.g. data/local/corrections/suppressions.yaml or preference_hints.json) that recommendation logic can read to “don’t recommend X” or “prefer Y when context Z.” This is new state.
- **Context trigger tuning:** Triggers are code-driven; no persisted “trigger weight” or “disable trigger T for job J.” Could add a small “trigger_overrides” or “trigger_suppressions” store (e.g. list of {trigger_type, job_id, suppress: true}) that trigger evaluation respects. New state.

So: **specialization** and **routine** and (with new stores) **suppressions/preference hints** and **trigger overrides** can absorb feedback. **Trust/approval** can only absorb advisory notes (trust_notes), not permission escalation.

## 3. Exact gap between “context-aware copilot” and “learning from operator correction”

- **No correction event schema:** There is no first-class “correction” with source (recommendation | plan | job_run | artifact | task_replay), reference id, operator action, category, original/corrected value, reason, eligibility for memory update, reversibility.
- **No correction capture:** Operator cannot record “I rejected this recommendation because …”, “this plan preview was wrong because …”, “this job’s default param was wrong,” “this output style was wrong.” No `corrections add` or equivalent.
- **No structured correction types:** No typed categories (wrong_recommendation_timing, bad_job_parameter_default, output_style_correction, trust_level_note, etc.) so we can’t route corrections to the right update target or block unsafe ones.
- **No learning rules:** No explicit rules that say “correction category X with evidence Y can propose update to target Z” or “category X cannot change trust_level or approval.”
- **No update preview/apply/reject:** Specialization is updated only via direct calls to update_from_operator_override / save_as_preferred; there is no “propose update from correction → preview → approve/reject” flow.
- **No reversible history:** update_history in specialization records “source” and “summary” but not “correction_id” or “update_id” or “revert_id.” We can’t revert “the update that came from correction corr_123.”
- **No impact visibility:** No report of “recent corrections,” “proposed updates,” “applied updates,” “reverted updates,” or “most corrected areas.”
- **No correction-to-eval bridge:** Repeated corrections on a job don’t surface as “review trust/benchmark recommended” in eval or mission control.

Filling this gap requires: (1) correction event schema and store, (2) correction types and validation, (3) capture surface (CLI + optional mission_control), (4) learning rules and propose-update logic, (5) update preview/apply/reject and reversible history, (6) impact visibility and correction-to-eval advisory.

## 4. File plan

| Module | Files | Purpose |
|--------|-------|--------|
| A | docs/M23M_READ_FIRST.md | This document. |
| B | corrections/schema.py | CorrectionEvent dataclass; SOURCE_TYPES, CORRECTION_CATEGORIES; validation. |
| B | corrections/config.py | get_corrections_root(repo_root) → data/local/corrections; events dir, updates dir. |
| B | corrections/store.py | save_correction(event), list_corrections(limit, filters), get_correction(correction_id); persist events as JSON under corrections/events/. |
| C | corrections/capture.py | add_correction(source_type, source_id, category, ...) → builds event, validates category, saves. |
| C | cli.py | corrections add --source recommendation|job|plan|routine|artifact|benchmark --id X --category Y ... ; corrections list; corrections show --id. |
| D | corrections/rules.py | LEARNING_RULES: which category can update which target (specialization_params, specialization_paths, specialization_output_style, routine_ordering, trust_notes, suppressions, trigger_suppressions); BLOCKED_TARGETS (no trust_level promotion, no approval grant); propose_updates(repo_root) → list of ProposedUpdate. |
| D | corrections/propose.py | propose_updates(): scan recent corrections, apply rules, return list of ProposedUpdate (update_id, correction_ids, target_type, target_id, before_value, after_value, risk_level, reversible). |
| E | corrections/updates.py | UpdateRecord (update_id, correction_ids, target_type, target_id, before, after, applied_at, reverted_at); save_update_record, load_update_record, apply_update(update_id, repo_root), revert_update(update_id, repo_root); preview_update(update_id). |
| E | cli.py | corrections propose-updates; corrections preview-update --id; corrections apply-update --id; corrections reject-update (record only, no state change). |
| F | corrections/history.py | list_applied_updates(limit), list_reverted_updates(limit), get_update_history(update_id); revert_update writes reverted_at and restores before state. |
| G | corrections/report.py | corrections_report(repo_root): recent corrections, proposed updates, applied, reverted, most_corrected_jobs, repeated_correction_alerts. |
| H | corrections/eval_bridge.py | advisory_review_for_corrections(corrections): return list of {job_id, recommendation: "review_trust"|"review_benchmark", reason}. Mission_control or eval board can surface these. |
| I | mission_control/state.py, report.py | Add block corrections: recent_count, proposed_updates_count, applied_count, reverted_count, review_recommended_jobs (from eval_bridge). |
| I | docs/M23M_CORRECTION_OPERATOR.md, M23M_FINAL_OUTPUT.md; tests/test_corrections.py | Operator doc; final output; tests for add, list, propose, preview, apply, reject, revert, rules, report, eval_bridge. |

## 5. Safety/risk note

- **No silent mutation:** Specialization (and any other target) is updated only via explicit apply-update after preview. Corrections are stored as events; proposed updates are derived by rules; apply is a separate operator action.
- **Blocked targets:** Learning rules must NOT allow corrections to: change trust_level from simulate_only to trusted_for_real, add approved_paths/approved_action_scopes, remove approval checks, or auto-promote jobs to real execution. trust_notes and “review recommended” advisories are allowed.
- **Reversibility:** Every applied update records before/after; revert restores before state and marks update as reverted. No hidden overwrites.
- **Local-only:** All under data/local/corrections. No cloud; no telemetry.
- **Typed categories:** Only allowed categories can drive proposed updates; unknown or unsafe categories are stored but do not produce updates.

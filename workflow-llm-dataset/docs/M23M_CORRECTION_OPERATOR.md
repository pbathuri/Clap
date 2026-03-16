# M23M — Operator correction loop — operator guide

What a correction is, how correction learning differs from hidden continual learning, what can and cannot be updated, how updates are reviewed and reverted, and how privacy/local-first/safety are preserved.

---

## 1. What a correction is

A **correction** is an explicit operator-recorded feedback event. It has:

- **Source:** recommendation, routine, plan_preview, job_run, artifact_output, task_replay, benchmark_result
- **Reference id:** e.g. recommendation_id, job_pack_id, plan_id, routine_id
- **Category:** e.g. wrong_recommendation_timing, bad_job_parameter_default, output_style_correction, trust_notes_correction, routine_ordering_correction, context_trigger_false_positive
- **Operator action:** rejected, corrected, accepted_with_note, skipped, deferred
- **Original / corrected value** and **reason**
- **Eligible for memory update:** only certain categories can drive proposed updates (see learning rules)

Corrections are stored under `data/local/corrections/events/` as JSON. They are **not** applied automatically to specialization, job packs, or routines.

---

## 2. How correction learning differs from hidden continual learning

- **Explicit capture:** You run `corrections add --source job --id X --category bad_job_parameter_default ...`. Nothing is learned until you record a correction.
- **Proposed updates:** `corrections propose-updates` scans eligible corrections and **proposes** updates (e.g. “set preferred_params for job X to …”). No state is changed yet.
- **Preview then apply:** You run `corrections preview-update --id upd_123` to see before/after, then `corrections apply-update --id upd_123` to apply. Learning is a deliberate step.
- **Reversible:** Every applied update stores before/after. `corrections revert-update --id upd_123` restores the previous state and marks the update as reverted.
- **No silent drift:** Specialization and job pack changes happen only through apply-update (or existing paths like `update_from_operator_override`). There is no background process that mutates memory from raw usage.

---

## 3. What can be updated from corrections

Learning rules allow these **targets** (only when the correction category matches):

- **specialization_params** — from category `bad_job_parameter_default` (corrected_value = dict of param key → value)
- **specialization_paths** — from `bad_path_app_preference`
- **specialization_output_style** — from `output_style_correction`
- **job_pack_trust_notes** — from `trust_notes_correction`, `trust_level_too_high`, `trust_level_too_low` (advisory note only; does **not** change trust_level)
- **routine_ordering** — from `routine_ordering_correction` (corrected_value = list of job_pack_ids in order)
- **trigger_suppression** — from `context_trigger_false_positive` / `context_trigger_false_negative` (stored in `data/local/corrections/trigger_suppressions.json` for trigger evaluation to respect)

---

## 4. What cannot be updated

- **trust_level:** Corrections cannot change a job from simulate_only to trusted_for_real or grant real execution. Blocked by design.
- **approval_registry:** Corrections cannot add approved_paths or approved_action_scopes. No privilege escalation.
- **real_mode_eligibility:** Cannot be turned on via corrections.

These are enforced in the learning rules (BLOCKED_TARGETS). Trust-level feedback is only used to propose **trust_notes** (advisory text) or to surface “review trust” in the correction-to-eval bridge.

---

## 5. How updates are reviewed and reverted

- **Propose:** `corrections propose-updates` writes proposed updates to `data/local/corrections/proposed/`. Each has update_id, target_type, target_id, before_value, after_value, risk_level.
- **Preview:** `corrections preview-update --id upd_123` shows exactly what would change. No side effects.
- **Apply:** `corrections apply-update --id upd_123` performs the change (e.g. writes specialization, updates job trust_notes, or routine ordering) and records the update in `data/local/corrections/updates/` with applied_at.
- **Reject:** `corrections reject-update --id upd_123` removes the proposed update file; no apply.
- **Revert:** `corrections revert-update --id upd_123` restores the stored before_value and sets reverted_at on the update record. Applied updates are reversible by design (except where we don’t store before state; currently all supported targets store before).

---

## 6. How privacy / local-first / safety are preserved

- **Local-only:** All correction events and update records live under `data/local/corrections/`. No cloud, no telemetry.
- **Inspectable:** Events and updates are JSON; you can audit what was corrected and what was applied.
- **No auto-apply:** Nothing is applied without an explicit `apply-update` (or existing specialization/job pack APIs you already use).
- **Approval/trust unchanged:** Corrections cannot bypass check_job_policy or the approval registry. Learning only adjusts preferred params, paths, output style, trust_notes, routine order, and trigger suppressions.

---

## 7. Correction-to-eval bridge

Repeated corrections for the same job or routine can surface **advisory** signals:

- **review_trust** — when there are trust-level-related corrections
- **review_benchmark** — when there are output/param/artifact corrections
- **review_trigger_policy** — when there are trigger false positive/negative corrections

Mission control shows `review_recommended` job/routine ids from this bridge. It does **not** auto-downgrade or auto-upgrade trust; it only suggests that an operator review trust or benchmark for that job.

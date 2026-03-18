# M47I–M47L — Quality Signals + Delightful Operator Guidance: Before Coding

## 1. What current guidance and quality-signaling already exists

| Area | What exists | Notes |
|------|-------------|--------|
| **mission_control/next_action** | `recommend_next_action(state)` → action, rationale, detail. Actions: build, benchmark, cohort_test, promote, hold, rollback, replay_task, observe_setup. Priority order: rollback → build (pending proposals) → promote → benchmark → cohort_test → build (unreviewed) → observe_setup → replay_task → hold. | No confidence score; no “ready now” vs “not safe yet”; rationale is one-line. |
| **conversational/explain** | `answer_what_next`, `answer_why_blocked`, `answer_why_this_project`, `answer_what_changed`. Uses mission_control state + next_action + project_case recommended_next_project_action. | Concatenates strings; no clarity/confidence; blocked answer points to portfolio/planner commands. |
| **agent_loop/next_step_engine** | `suggest_next_steps(context_bundle)` → AgentResponse with steps, evidence, confidence; appends “[Evidence is weak; recommendations are generic.]” when confidence < 0.5. | Confidence and evidence present but not surfaced as first-class quality signals. |
| **supervised_loop/next_action** | `propose_next_actions(project_slug)` → list of QueuedAction + BlockedCycleReason. Resume awaiting_approval first, then compile plan, etc. | Why text on actions (e.g. “Run is paused at checkpoint”); no clarity score. |
| **executor** | `get_recovery_options(run_id)` → retry/skip/substitute + suggested_bundles; `resume_from_blocked`. Message: “Use: executor resume-from-blocked …”. | Recovery path exists; phrasing is technical. |
| **vertical_packs/playbooks** | `get_operator_guidance_when_stalled(curated_pack_id, blocked_step_index)` → guidance, commands, recovery_path, failure_entry (symptom, remediation_hint, escalation_command). | Strong vertical-specific recovery; not aggregated into a single “best recovery” signal. |
| **progress/recovery** | `build_stalled_recovery`, `format_stalled_recovery`; playbook matching by cause_codes/keywords. | Board + playbook; output is sectioned text, not quality-signaled. |
| **production_launch** | Post-deployment guidance (continue/narrow/rollback/repair), recommended_actions, reason. Stability decision packs with rationale and evidence_refs. | Evidence-linked; no “ambiguity” or “weak guidance” flag. |
| **signal_quality** | `score_queue_item`, `score_assist_suggestion` → SignalQualityScore (urgency, usefulness, noise, interruption_cost, is_urgent_tier). | Scores for queue/assist; not applied to “guidance” as a surface. |
| **vertical_launch** | Launch kits, operator playbook (setup_guidance, first_value_coaching, common_recovery_guidance, when_to_narrow_scope). Rollout review decision + rationale. | Rich operator copy; not folded into a single “next best action” or “ready/not ready” signal. |

## 2. Where ambiguity or low-confidence guidance remains

- **Next action**: mission_control next_action returns “hold” with “No urgent signal; review mission-control state and choose next step”—vague. No indication when the recommendation is low-confidence.
- **What next (conversational)**: Combines next_action + project_case suggested action without a single clarity score or “weak evidence” surface.
- **Blocked state**: answer_why_blocked and recovery flows point to commands (portfolio blocked, progress recovery, planner preview) but do not produce a single “best recovered blocked state” or “strongest next step to unblock.”
- **Review-needed**: “Pending proposals need operator review” and unreviewed workspaces appear in next_action; no dedicated “needs-review” signal with confidence or priority.
- **Resume guidance**: Supervised loop proposes “Resume executor run X” with why; executor recovery options are command-centric; no “ready to act” vs “needs more info” distinction.
- **Operator routine**: Continuity carry-forward, production review cycles, sustained-use checkpoints exist but are not summarized as “operator routine guidance” with clarity/confidence.
- **Support/recovery**: Vertical playbook recovery and executor recovery exist separately; no unified “best recovery phrasing” or “evidence-linked confidence” for the chosen vertical.
- **Generic fallbacks**: Next-step engine’s “Not enough project or workflow evidence yet…” and “[Evidence is weak; recommendations are generic.]” are explicit but not modeled as weak-guidance warnings or ambiguity warnings.

## 3. Exact file plan

| Area | Path | Purpose |
|------|------|--------|
| Doc | `docs/M47I_M47L_QUALITY_SIGNALS_GUIDANCE_BEFORE_CODING.md` | This file. |
| Models | `src/workflow_dataset/quality_guidance/models.py` | QualitySignal, ClarityScore, ConfidenceWithEvidence, AmbiguityWarning, ReadyToActSignal, NeedsReviewSignal, StrongNextStepSignal, WeakGuidanceWarning, GuidanceItem. |
| Signals | `src/workflow_dataset/quality_guidance/signals.py` | Build quality signals from mission_control next_action, project_case, supervised_loop, executor recovery, vertical playbook, progress recovery (read-only). |
| Guidance | `src/workflow_dataset/quality_guidance/guidance.py` | next_best_action_guidance(), review_needed_guidance(), blocked_state_guidance(), resume_guidance(), operator_routine_guidance(), support_recovery_guidance(); each returns GuidanceItem(s) with quality signals. |
| Surfaces | `src/workflow_dataset/quality_guidance/surfaces.py` | ready_now_states(), not_safe_yet_states(), ambiguity_report(), weak_guidance_report(); concise rationale and evidence-linked confidence. |
| Store | `src/workflow_dataset/quality_guidance/store.py` | Optional: persist guidance items by id for explain --id; data/local/quality_guidance/. |
| CLI | `src/workflow_dataset/cli.py` | quality-signals; guidance next-action; guidance explain --id; guidance ambiguity-report. |
| Mission control | `src/workflow_dataset/mission_control/state.py` | quality_guidance slice: strongest_ready_to_act, most_ambiguous_guidance, best_recovered_blocked_state, weakest_guidance_surface, next_recommended_guidance_improvement. |
| Tests | `tests/test_quality_guidance.py` | Quality signal generation, ambiguity warning, ready-to-act vs needs-review, blocked-state recovery, weak-guidance handling, low-evidence cases. |
| Deliverable | `docs/M47I_M47L_QUALITY_SIGNALS_GUIDANCE_DELIVERABLE.md` | Files, CLI, samples, tests, gaps. |

## 4. Safety/risk note

- **Do not fake certainty**: When evidence is weak, clarity score and confidence must remain low; use weak_guidance_warning and ambiguity_warning so the operator sees uncertainty.
- **Do not increase noise**: Adding a quality layer must not duplicate or contradict mission_control/assist/review_studio; we aggregate and add signals, not replace.
- **Do not broaden beyond vertical**: Guidance and “feels excellent” surfaces are scoped to the chosen vertical where applicable (vertical_launch, vertical_packs); fallbacks remain generic but labeled.

## 5. Quality-signal principles

- **Sharper and more confident when evidence supports it**: Strong evidence → higher clarity score, confidence-with-evidence, ready-to-act or strong-next-step.
- **Reduce ambiguity**: Explicit ambiguity warnings when intent or next step is unclear; suggest concrete follow-up (e.g. “Specify project id” or “Run X to get evidence”).
- **Trust through clarity**: Concise rationale and evidence_refs so the operator can verify; avoid vague “review state” without a specific action.
- **Intentional support/review paths**: Recovery and review-needed guidance should reference specific commands or playbook steps and “ready now” vs “not safe yet” where applicable.
- **Calmness + usefulness**: Fewer generic recommendations; more “do this one thing” when we have one strong signal; otherwise “do A or B” with priority.

## 6. What this block will NOT do

- Rebuild workspace shell, mission control, queue/day shell, assist engine, review studio, or support/reliability systems.
- Replace mission_control next_action or conversational explain; we consume them and add a quality/guidance layer on top.
- Marketing copywriting or purely visual redesign.
- Remove nuance where uncertainty is real; we surface uncertainty explicitly (weak-guidance, ambiguity).
- Auto-execute or change executor/supervisory behavior; guidance remains recommendation-only.

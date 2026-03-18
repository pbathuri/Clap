# M31I–M31L Personal Adaptation Loop — Pre-Coding Analysis

## 1. What preference/style/adaptation logic already exists

- **personal/preference_model.py**: `PreferenceRecord` (key, value, source=teaching|inferred); `get_preference` / `set_preference` are stubs with no persistence.
- **personal/style_profiles.py**: `StyleProfile` (profile_id, profile_type, domain, evidence_count, confidence, naming/folder/export/spreadsheet patterns, session_id, project_id). `aggregate_naming_style`, `aggregate_folder_structure_style`, `build_profiles_from_style_signals`, `save_style_profile`, `load_style_profiles`. No review status or “accepted preference update” record.
- **personal/style_suggestion_engine.py**: `StyleAwareSuggestion` (suggestion_id, type, title, description, rationale, confidence_score, status=pending|accepted|dismissed). `generate_style_aware_suggestions` from context + style_profiles + imitation_candidates + routines. Suggestions are not yet turned into applied preferences that affect pack defaults or output framing.
- **personal/imitation_candidates.py**: `ImitationCandidate` (candidate_id, project_id, domain, candidate_type, evidence, confidence_score). `collect_candidates_from_profiles`; no link to “apply to surface” or review flow.
- **personal/work_graph.py**: NodeTypes include PREFERENCE, STYLE_PATTERN, STYLE_PROFILE, IMITATION_CANDIDATE, STYLE_AWARE_SUGGESTION. Graph add_node; no unified “preference candidate” with review_status and affected_surface.
- **personal/profile_builder.py**: `build_profile_from_observation`, `update_profile_from_teaching` — stubs.
- **corrections**: `CorrectionEvent` (source_type, correction_category, original/corrected_value, eligible_for_memory_update). `propose_updates` → `ProposedUpdate` (target_type, target_id, before/after_value) with LEARNING_RULES (specialization_params, specialization_paths, specialization_output_style, job_pack_trust_notes, routine_ordering, trigger_suppression). Proposals are for job/specialization/routine updates, not a generic “preference candidate” or “style pattern candidate” with explicit apply to pack/output/workspace/notification.
- **teaching**: `Skill` (skill_id, source_type, status draft|accepted|rejected); skill_store. No direct connection to preference/style application surfaces.

So: **existing** = preference record model (stub), style profiles with evidence/confidence, style-aware suggestions with status, imitation candidates, corrections → proposed updates to specializations/job packs/routines. **Missing** = unified preference/style *candidates* with review_status and affected_surface, *accepted preference update* record, *application layer* that applies only accepted items to pack defaults / output framing / workspace presets / notifications, and CLI/reports for preferences, style-candidates, apply-preference, explain-preference.

---

## 2. What is missing for a real personal adaptation loop

- **Explicit models**: Preference candidate (key, proposed_value, confidence, evidence, affected_surface, review_status); style pattern candidate (pattern_id, description, evidence, confidence, affected_surface, review_status); accepted preference/profile update (update_id, candidate_id, applied_at, applied_surface).
- **Inference/candidate generation**: One place that produces preference and style candidates from: observed work (routines, style signals), repeated corrections (output_style, path preference, etc.), routine confirmations, accepted teaching artifacts. Confidence and evidence attached to each candidate.
- **Application layer**: Apply *only* accepted preferences to: pack defaults, output framing, workspace presets, suggested actions, notification/review emphasis. No silent apply of unreviewed candidates.
- **CLI**: `personal preferences`, `personal style-candidates`, `personal apply-preference --id <id>`, `personal explain-preference --id <id>`.
- **Mission control**: Additive visibility for new preference candidates, accepted adaptations, low-confidence candidates needing review, strongest learned patterns.
- **Explain**: For any candidate, show evidence, reasoning, and affected surface in operator-facing form.

---

## 3. Exact file plan

| Area | Action | Path |
|------|--------|------|
| Models | Create | `src/workflow_dataset/personal_adaptation/models.py` — PreferenceCandidate, StylePatternCandidate, AcceptedPreferenceUpdate; review_status; affected_surface enum/constants |
| Candidates | Create | `src/workflow_dataset/personal_adaptation/candidates.py` — generate_preference_candidates (from corrections, routines, style profiles, teaching), generate_style_candidates; evidence/confidence |
| Store | Create | `src/workflow_dataset/personal_adaptation/store.py` — save_candidate, list_candidates, accept_candidate → write AcceptedPreferenceUpdate, list_accepted |
| Apply | Create | `src/workflow_dataset/personal_adaptation/apply.py` — apply_accepted_preference(update_id) → apply to pack_defaults / output_framing / workspace_preset / suggested_actions / notification_style (surfaces); read-only where no write API exists |
| Explain | Create | `src/workflow_dataset/personal_adaptation/explain.py` — explain_preference(candidate_id) → evidence, reasoning, affected_surface text |
| Init | Create | `src/workflow_dataset/personal_adaptation/__init__.py` |
| CLI | Modify | `src/workflow_dataset/cli.py` — add personal_group: preferences, style-candidates, apply-preference --id, explain-preference --id |
| Mission control | Modify | `src/workflow_dataset/mission_control/state.py` — add personal_adaptation block (candidates_count, accepted_count, low_confidence_count, strongest_patterns) |
| Mission control report | Modify | `src/workflow_dataset/mission_control/report.py` — add [Personal adaptation] section |
| Tests | Create | `tests/test_personal_adaptation.py` |
| Docs | Create | `docs/M31I_M31L_PERSONAL_ADAPTATION.md` |

---

## 4. Safety/risk note

- **No silent apply**: Application only after operator accepts a candidate; no automatic application of inferred preferences.
- **Inspectable**: All candidates and accepted updates stored locally with evidence and affected_surface; explain-preference exposes reasoning.
- **No trust bypass**: Application layer does not change trust levels, approval registry, or real-mode eligibility; only pack defaults, output style, workspace presets, and similar surfaces that are already allowed to be user-configurable.
- **No opaque drift**: Preferences and style patterns are explicit records; no hidden continual self-modification.

---

## 5. What this block will NOT do

- **No hidden continual self-modification** or silent personality drift.
- **No opaque fine-tuning** from all observed data; only structured candidates with evidence and review.
- **No rebuild** of packs, copilot, or corrections; integration via existing list_corrections, propose_updates, style_profiles, imitation_candidates, teaching skills.
- **No automatic application** of unreviewed candidates.
- **No change** to trust levels or approval boundaries from this layer.

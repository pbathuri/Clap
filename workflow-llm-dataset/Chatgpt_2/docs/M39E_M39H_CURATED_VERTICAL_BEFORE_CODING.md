# M39E–M39H — Curated Vertical Workflow Packs: Before Coding

## 1. What pack/template/workflow assets already exist

### Packs
- **pack_models.py**: `PackManifest` (pack_id, name, version, role_tags, industry_tags, workflow_tags, task_tags, supported_modes, safety_policies, behavior).
- **Pack registry**: install, resolve, activate, conflict resolution, gallery, certification, behavior_runtime.
- **Physical packs**: `packs/founder_ops_pack/`, `packs/ops_reporting_pack/` (manifests, trials, retrieval profiles).

### Value packs
- **value_packs/models.py**: `ValuePack` (pack_id, name, target_field, target_job_family, starter_kit_id, domain_pack_id, recommended_profile_defaults, recommended_job_ids, recommended_routine_ids, first_value_sequence, first_simulate_only_workflow, first_trusted_real_candidate, approvals_likely_needed, benchmark_trust_notes).
- **FirstValueStep**: step_number, title, command, what_user_sees, what_to_do_next, run_read_only.
- **value_packs/registry.py**: `get_value_pack`, `list_value_packs`.
- **value_packs/golden_bundles.py**: `GoldenFirstValueBundle` per pack (steps, sample_input_refs, example_job_id, first_simulate_command, first_real_command); founder_ops_plus, analyst_research_plus, developer_plus, document_worker_plus.
- **value_packs/first_run_flow.py**: `build_first_run_flow(pack_id)` → steps, pack.
- **CLI**: `value-packs list`, `value-packs show --id`, `value-packs recommend`, `value-packs first-run --id`, `value-packs compare`, `value-packs golden-bundle --id`.

### Templates
- **templates/registry.py**: List/load templates; VALID_WORKFLOW_IDS (weekly_status, status_action_bundle, etc.); WORKFLOW_ARTIFACTS, ARTIFACT_TO_FILENAME.
- **templates/harness.py**, parameters, validation, export_import.

### Planner / Executor
- **planner/schema.py**: GoalRequest, Plan, Checkpoint, BlockedCondition, ExpectedArtifact, step classes (reasoning_only, sandbox_write, trusted_real_candidate, etc.).
- **planner/compile.py**, classify, sources, store, preview, explain.
- **executor/models.py**, runner, hub, mapping, bundles.

### Teaching
- **teaching/skill_models.py**, skill_store, scorecard, report, review, normalize.

### Workspace
- **workspace/state.py**, models, home, navigation, presets, cli.
- **default_experience**: SurfaceClassification (default_visible, advanced, expert), DefaultWorkdayModeSet, DefaultExperienceProfile; profiles (first_user, calm_default, full, founder_calm, analyst_calm, developer_calm, document_heavy_calm, supervision_heavy_calm); surfaces (workspace_home, day_status, queue_summary, approvals_urgent, continuity_carry_forward, mission_control, trust_cockpit, etc.).

### Queue / Continuity / Operator / Trust
- **unified_queue/models.py**: UnifiedQueueItem, QueueSection, SourceSubsystem, ActionabilityClass, RoutingTarget; collect, prioritize, views, summary.
- **continuity_engine**: store (last_session, last_shutdown, carry_forward, next_session), resume_flow, morning_flow, shutdown_flow, models.
- **operator_mode**: DelegatedResponsibility, OperatorModeProfile, ResponsibilityBundle, PauseState, SuspensionRevocationState, OperatorModeSummary; store, bundles, pause_revocation, explain.
- **trust**: tiers, presets (cautious, supervised_operator, bounded_trusted_routine, release_safe), contracts, eligibility, scope, validation_report.

### Workday
- **workday/models.py**: WorkdayState, state machine.
- **workday/presets.py**: WorkdayPreset (default_day_states, default_transition_after_startup, queue_review_emphasis, operator_mode_usage, quick_actions, role_operating_hint); founder_operator, analyst, developer, document_heavy, supervision_heavy.

### Docs
- **docs/packs/**: FIRST_ROLE_PACK_SCOPE, FIRST_ROLE_PACK_DEMO.
- **docs/M37A_M37D_DEFAULT_EXPERIENCE.md**, M37D1_ONBOARDING_AND_DISCLOSURE, M36D1_WORKDAY_PRESETS_AND_ROLES, M35D1_TRUST_PRESETS_AND_ELIGIBILITY, M36I_M36L_CONTINUITY_ENGINE, M38*, value-pack–related content in integration reports.

---

## 2. What is missing for true curated vertical flows

- **Single “curated vertical pack” abstraction** that bundles: one value pack + one workday preset + one default-experience (calm) profile + one trust preset + recommended queue/continuity/operator settings. Today these are separate; no “apply founder_operator_core” that sets all at once.
- **Explicit “core workflow path” and “first-value path”** with entry point, required surfaces, suggested next actions, first-value milestone, and common failure points. Value packs have first_value_sequence but no “path” object with failure points or required surfaces.
- **Success milestones** as first-class objects (e.g. “first meaningful project setup”, “first safe operator routine”) with progress tracking. Golden bundles have steps but no milestone or progress store.
- **Required vs optional surfaces** per vertical: which surfaces must be visible/used for this vertical vs optional. Default experience has default_visible/advanced/expert but not “required for vertical X”.
- **Recommended workday profile** and **recommended queue profile** (e.g. calmness, section ordering, emphasis) per vertical. Workday presets exist but are not tied to a curated pack or path.
- **Recommended automation/operator settings** and **vertical-specific review/audit posture** in one place. Operator bundles and trust presets exist but are not bundled per vertical.
- **CLI**: `vertical-packs list/show/apply`, `vertical-paths first-value --id`, and **mission control** visibility for active curated pack, first-value path progress, next milestone, blocked onboarding step, strongest value path.
- **Vertical/scope-lock layer**: No dedicated Pane 1 “vertical” or “scope lock” package was found in the repo; this deliverable will create the curated vertical layer that can later integrate with scope-lock if added.

---

## 3. Exact file plan

| Action | Path |
|--------|------|
| Create | `src/workflow_dataset/vertical_packs/models.py` — CuratedVerticalPack, CoreWorkflowPath, FirstValuePath, TrustReviewPosture, RecommendedWorkdayProfile, RecommendedQueueProfile, RequiredSurfaces, SuccessMilestone. |
| Create | `src/workflow_dataset/vertical_packs/paths.py` — Guided path definitions: entry_point, required_surfaces, suggested_next_actions, first_value_milestone, common_failure_points; build_path_for_pack(pack_id). |
| Create | `src/workflow_dataset/vertical_packs/defaults.py` — Vertical-specific defaults: queue/calmness, operator, review/audit; apply_vertical_defaults(pack_id, repo_root). |
| Create | `src/workflow_dataset/vertical_packs/registry.py` — BUILTIN_CURATED_PACKS, get_curated_pack(pack_id), list_curated_pack_ids(); map value_pack_id → curated pack. |
| Create | `src/workflow_dataset/vertical_packs/store.py` — Persist active pack and path progress (data/local/vertical_packs/active.json, progress.json); get_active_pack, set_active_pack, get_path_progress, set_milestone_reached. |
| Create | `src/workflow_dataset/vertical_packs/progress.py` — First-value milestone tracking: which milestones reached, next milestone, blocked step, strongest path. |
| Create | `src/workflow_dataset/vertical_packs/__init__.py` — Re-export models, registry, paths, defaults, store, progress. |
| Modify | `src/workflow_dataset/cli.py` — Add `vertical-packs` Typer: list, show --id, apply --id; add `vertical-paths` (or under vertical-packs): first-value --id; optional --json. |
| Modify | `src/workflow_dataset/mission_control/state.py` — Add `vertical_packs_state`: active_curated_pack_id, current_first_value_path_id, next_vertical_milestone, blocked_vertical_onboarding_step, strongest_value_path_id. |
| Modify | `src/workflow_dataset/mission_control/report.py` — Print vertical_packs_state when present. |
| Create | `tests/test_vertical_packs.py` — test_curated_pack_model, test_guided_path_generation, test_vertical_defaults_apply, test_first_value_milestone_tracking, test_weak_incomplete_path_behavior. |
| Create | `docs/samples/M39_curated_vertical_pack_sample.json` — One full curated pack (e.g. founder_operator_core). |
| Create | `docs/samples/M39_guided_value_path_sample.json` — One first-value path with milestones and failure points. |
| Create | `docs/samples/M39_milestone_progress_sample.json` — Sample progress output. |
| Create | `docs/M39E_M39H_CURATED_VERTICAL_DELIVERABLE.md` — Files modified/created, CLI usage, samples, tests, remaining gaps. |

---

## 4. Safety / risk note

- **Apply** will change user-facing state (active pack, possibly workday/trust/experience profile). We do not auto-apply trust or approval scope; we only set recommended defaults and persist “active pack” and path progress. High-impact defaults (e.g. trust preset) should remain explicit or gated (e.g. “apply --dry-run” then “apply --confirm”).
- **No new execution or network**: vertical_packs only orchestrates existing CLI/APIs (value_packs, workday, default_experience, trust) and persists preferences. No new sandbox escape or data exfiltration surface.
- **Data**: Store under `data/local/vertical_packs/`; no PII. Progress and active pack are local only.

---

## 5. Curation principles

- **One primary vertical (founder/operator), few secondaries (analyst, developer, document_worker)** so the first-draft layer stays focused and “built for my work” for those roles.
- **Reuse over reinvention**: Curated pack = value_pack_id + workday_preset_id + default_experience_profile_id + trust_preset_id + optional queue/continuity/operator hints. No duplicate pack definitions.
- **Path-to-value over feature sprawl**: Each path has a clear first-value milestone and suggested next actions; common failure points are documented so we can later add remediation.
- **Trust/review visible**: Trust and review posture are explicit fields; we do not hide “this vertical recommends supervised_operator” or “approvals likely needed”.

---

## 6. What this block will NOT do

- **No scope creep**: Only the chosen verticals (founder_operator, analyst, developer, document_worker); no new verticals beyond mapping existing value packs to curated packs.
- **No rebuild of pack/runtime**: General pack registry, executor, planner, queue, continuity, operator mode, trust remain unchanged; we only add a layer that references them.
- **No new parallel curated “experiences”**: We add one curated layer (vertical_packs) that sits above value_packs and workday/default_experience/trust; we do not add a second competing “experience” system.
- **No hiding trust/review**: Recommended trust preset and review posture are part of the pack and paths; apply does not silently relax trust without user visibility.
- **No polish-first**: First-draft quality; no UI beyond CLI and mission-control report; no localization or accessibility pass.

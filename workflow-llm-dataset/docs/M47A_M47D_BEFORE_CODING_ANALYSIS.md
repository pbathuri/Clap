# M47A–M47D Before-Coding Analysis — Vertical UX Tightening + First-Value Compression

## 1. What current first-value and top-level vertical path already looks like

- **Production cut:** `get_active_cut()` returns the locked production cut with `chosen_vertical` (vertical_id, primary_workflow_ids, allowed_roles, non_core_surface_ids). When no cut: operator must run `production-cut lock --id <vertical_id>`.
- **Vertical packs:** `vertical_packs.paths.build_path_for_pack(pack_id)` returns `FirstValuePath` (entry_point, steps, milestones, suggested_next_actions, first_value_milestone_id, common_failure_points). Uses value_packs golden bundles or `value_packs.first_run_flow.build_first_run_flow(pack_id)`. Active pack from `vertical_packs.store.get_active_pack()` → `active_curated_pack_id` (defaults to founder_operator_core in vertical_speed when missing).
- **Operator quickstart:** `operator_quickstart.first_value_flow.build_first_value_flow()` returns a fixed 6-step flow (bootstrap profile, runtime, onboard, jobs list, inbox, run one simulate). Not yet scoped to chosen vertical; same for all.
- **Vertical speed:** `vertical_speed.identification._active_vertical_pack_id()` uses `get_active_pack()` → founder_operator_core fallback. Friction: `vertical_speed.friction.build_friction_clusters()`, speed-up candidates, repeat-value bottlenecks; mission_control slice exposes highest_frequency_workflow, biggest_friction_cluster, next_recommended_friction_reduction_action.
- **Mission control next_action:** `recommend_next_action(state)` is product/eval/incubator/cohort oriented (build, benchmark, promote, hold, rollback, observe_setup, replay_task). It does **not** recommend vertical-specific “next step on first-value path” or “clear blocked first-value.”

**Top-level path today:** Entry is diffuse (profile bootstrap, package first-run, value-packs first-run, quickstart, production-cut lock). First useful artifact path exists per pack via `build_path_for_pack`, but there is no single “start here” flow that is explicitly narrowed to the chosen vertical and no unified “current first-value stage” or “blocked first-value” signal.

## 2. Where friction or ambiguity remains

- **No single “start here” for chosen vertical:** User can land on profile bootstrap, onboard, value-packs first-run, or production-cut lock without a clear ordering or one obvious entry when a production cut is set.
- **Chosen vertical vs active pack:** Production cut (chosen vertical) and vertical_packs active pack can diverge; vertical_speed uses active pack, production-cut CLI uses cut. Excellence layer should prefer production cut when present so the “chosen vertical” is authoritative.
- **Next-step not vertical-scoped:** mission_control `recommend_next_action` does not use first-value path step index or “blocked at step N” to suggest the next command for the primary vertical.
- **Blocked first-value not surfaced:** Common failure points exist on `FirstValuePath`, but there is no aggregated “blocked first-value cases” or “missing next step” in mission control.
- **Repeat-value vs first-value:** Vertical speed addresses repeat-value (friction, compression); first-value compression (fewer steps to first artifact, first review, first routine) is only partially covered by existing paths and not tied to a single “excellence” report.

## 3. Exact file plan

- **New package:** `src/workflow_dataset/vertical_excellence/` (no rebuild of production_cut, vertical_packs, vertical_speed, operator_quickstart).
- **vertical_excellence/models.py:** FirstValuePathStage, RepeatValuePathStage, CriticalUserJourney, FrictionPoint, AmbiguityPoint, MissingNextStepSignal, ExcellenceTarget (dataclasses).
- **vertical_excellence/path_resolver.py:** `get_chosen_vertical_id(repo_root)` (production_cut first, then active pack, then default). `build_first_value_path_for_vertical(vertical_id, repo_root)` (delegate to vertical_packs.paths.build_path_for_pack or operator_quickstart first_value_flow when pack missing). `build_repeat_value_path_for_vertical(vertical_id, repo_root)` (use vertical_speed frequent workflows / repeat value).
- **vertical_excellence/compression.py:** `assess_first_value_stage(repo_root)` (current step index or “not started” / “completed”), `list_friction_points(repo_root)`, `list_ambiguity_points(repo_root)` (e.g. “no clear next after step 3”), `list_blocked_first_value_cases(repo_root)` (from failure points + state).
- **vertical_excellence/recommend_next.py:** `recommend_next_for_vertical(repo_root)` → command + label + rationale, preferring “next step on first-value path” or “recover from blocked” when applicable.
- **vertical_excellence/reports.py:** `format_first_value_path_report`, `format_friction_point_report`, `format_recommend_next`.
- **vertical_excellence/mission_control.py:** Slice: current_first_value_stage, strongest_friction_point_id, top_default_path_improvement, next_recommended_excellence_action, blocked_first_value_cases_count.
- **vertical_excellence/__init__.py:** Exports.
- **cli.py:** New group `vertical_excellence` with commands: `first-value`, `path-report`, `friction-points`, `recommend-next`.
- **mission_control/state.py:** Add `vertical_excellence_state` from slice (additive).
- **mission_control/report.py:** Add “[Vertical excellence]” section (additive).
- **tests/test_vertical_excellence.py:** Tests for path resolution, first-value stage, friction listing, recommend-next, no-active-vertical / no-active-project cases.
- **docs/M47A_M47D_VERTICAL_EXCELLENCE_DELIVERABLE.md:** File list, CLI, sample outputs, tests, gaps.

## 4. Safety/risk note

- **Read-only aggregation:** Vertical excellence layer only reads production_cut, vertical_packs, vertical_speed, mission_control state; it does not change cut, pack, or approvals. Recommend-next suggests commands; it does not execute them.
- **No broadening:** New CLI group is additive; default path tightening is via clearer “recommend next” and reports, not by removing or hiding existing commands.
- **Chosen vertical authority:** When production cut is set, we use its vertical_id for path and recommendations so the deployment stays aligned with the locked cut.

## 5. Vertical-excellence principles

- **Purpose-built feel:** One clear “start here” and “do this next” for the chosen vertical.
- **Compress time-to-first-value:** Surface the shortest path to first artifact / first review / first routine and highlight blocked steps and recovery.
- **Reduce cognitive overhead:** Fewer non-core choices in the default path; recommend-next returns one primary suggestion with rationale.
- **Strengthen repeat-value:** Reuse vertical_speed friction and repeat-value signals so excellence layer speaks to both first-value and repeat-value in one place.

## 6. What this block will NOT do

- **No broad redesign** across all verticals; only primary (chosen) vertical.
- **No cosmetic-only** UI work; focus on path model, compression, and recommend-next.
- **No reopening** experimental surfaces in the default path.
- **No execution** of recommended commands; suggestion only.
- **No replacement** of production_cut, vertical_packs, vertical_speed, or operator_quickstart; only a thin excellence layer on top.

# M46H.1 — Maintenance Profiles + Safe Repair Bundles: Deliverable

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/repair_loops/models.py` | Added `RepairGuidanceKind`, `RepairGuidance`; added `maintenance_profile_id`, `repair_bundle_id`, `operator_guidance` to `RepairLoop` and `to_dict`. |
| `src/workflow_dataset/repair_loops/store.py` | Import and load/save `RepairGuidance`; `_dict_to_guidance`; `load_repair_loop` sets `maintenance_profile_id`, `repair_bundle_id`, `operator_guidance`. |
| `src/workflow_dataset/repair_loops/flow.py` | `_guidance_for_proposal(pattern_id, profile_id, bundle_id)`; `propose_repair_plan` accepts `maintenance_profile_id`, `repair_bundle_id`, `pattern_id` and sets guidance on loop. |
| `src/workflow_dataset/repair_loops/signal_to_repair.py` | `propose_plan_and_pattern_from_signal(...)` returns `(plan, pattern_id)` for use with profiles/bundles. |
| `src/workflow_dataset/repair_loops/__init__.py` | Exported `RepairGuidance`, `RepairGuidanceKind`, `propose_plan_and_pattern_from_signal`, profiles and bundles APIs. |
| `src/workflow_dataset/cli.py` | `repair-loops propose`: added `--profile`, `--bundle`, use `propose_plan_and_pattern_from_signal`, pass profile/bundle/pattern_id to `propose_repair_plan`, print guidance. `repair-loops show`: print `maintenance_profile_id`, `repair_bundle_id`, `operator_guidance`. Added `repair-loops profiles` and `repair-loops bundles` (list + show by --id). |
| `tests/test_repair_loops.py` | Added `test_maintenance_profiles`, `test_safe_repair_bundles`, `test_propose_with_profile_and_guidance`, `test_propose_with_bundle`. |

## 2. Files created

| File | Purpose |
|------|---------|
| `src/workflow_dataset/repair_loops/profiles.py` | `MaintenanceProfile` model; built-in profiles: light_touch, balanced, production_strict; `get_maintenance_profile`, `list_maintenance_profile_ids`; `is_pattern_allowed`, `requires_council`, `guidance_for_pattern`. |
| `src/workflow_dataset/repair_loops/bundles.py` | `SafeRepairBundle` model; built-in bundles: queue_memory_baseline, degraded_runtime_recovery, approval_planner_recovery, automation_feature_safety, install_benchmark_recovery; `get_safe_repair_bundle`, `list_safe_repair_bundle_ids`, `bundle_first_plan`, `bundle_pattern_ids_for_signal`. |
| `docs/samples/M46H1_maintenance_profile.json` | Sample balanced maintenance profile. |
| `docs/samples/M46H1_safe_repair_bundle.json` | Sample safe repair bundle (queue_memory_baseline). |
| `docs/M46H1_MAINTENANCE_PROFILES_BUNDLES_DELIVERABLE.md` | This deliverable. |

## 3. Sample maintenance profile

**balanced** (see `docs/samples/M46H1_maintenance_profile.json`):

- **profile_id**: balanced  
- **name**: Balanced  
- **description**: Mix of do-now (queue, memory refresh) and schedule-later (runtime reset, automation pause).  
- **allowed_pattern_ids**: ["*"]  
- **require_council_for_pattern_ids**: ["benchmark_refresh_rollback", "degraded_feature_quarantine"]  
- **do_now_pattern_ids**: ["queue_calmness_retune", "memory_curation_refresh", "continuity_resume_reconciliation"]  
- **schedule_later_default_reason**: "Run in next maintenance window."  
- **max_actions_without_council**: 0  

## 4. Sample safe repair bundle

**queue_memory_baseline** (see `docs/samples/M46H1_safe_repair_bundle.json`):

- **bundle_id**: queue_memory_baseline  
- **name**: Queue + memory baseline  
- **description**: Re-establish queue calmness and memory curation baseline. Low risk.  
- **pattern_ids**: ["queue_calmness_retune", "memory_curation_refresh"]  
- **do_now_guidance**: "Safe to run now; read-heavy and non-destructive."  
- **schedule_later_guidance**: "If system is under load, run in next quiet window."  
- **operator_summary**: "Do now: queue summary + calmness review, then memory curation refresh. Schedule later only if under load."  
- **signal_hints**: (drift, queue), (drift, memory_curation)  

## 5. Exact tests run

```bash
pytest tests/test_repair_loops.py -v
```

- **20 tests** (16 existing + 4 M46H.1): repair loop model, patterns, signal→plan, store, flow, mission control, no-known-repair, execute without approve; **maintenance_profiles**, **safe_repair_bundles**, **propose_with_profile_and_guidance**, **propose_with_bundle**.

## 6. Next recommended step for the pane

- **Persist active profile per repo**: Store the operator-selected maintenance profile (e.g. `data/local/repair_loops/active_profile`) and use it as default in `repair-loops propose` when `--profile` is omitted, so "do now vs schedule later" is consistent without passing `--profile` every time.  
- **Mission control**: Surface active profile and "next recommended maintenance (do-now)" in the mission control repair-loops slice (e.g. from profile + latest drift/signal).  
- **Council wiring**: For profiles that set `require_council_for_pattern_ids`, optionally require a council review outcome before `repair-loops execute` (e.g. check `council/reviews` or a repair-specific review) so production-strict is enforced in flow.

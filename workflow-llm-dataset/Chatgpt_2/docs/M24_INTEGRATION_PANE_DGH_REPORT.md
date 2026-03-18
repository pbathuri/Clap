# M24 Integration Pane — M24D–M24G.1, M24E–M24H.1, M24F–M24I.1

Safe integration of three milestone blocks in order: Pane 1 (Local Capability Activation), Pane 2 (Domain Specialization Provisioning), Pane 3 (Rollout / Demo / Support Productization).

---

## 1. Merge steps executed

- **Single-branch state:** Repo on `feat/ops-product-next-integration` with no separate pane branches. Integration was **logical**: verify each block’s surface in dependency order and run validation. No git merge commits.
- **Step 1 (Pane 1 — M24D–M24G.1):** Verified activation block present: `external_capability/*` (schema, registry, policy, planner, plans, activation_store, preview, executor, lifecycle, health, compatibility); CLI `capabilities external` (list, recommend, plan, blocked, explain, **compatibility**, **recommend-pack**, request, preview, execute, disable, history, **list-requests**, **health**); mission_control `external_capabilities` + `activation_executor` with `recommended_next_capability_action`. No conflicts; no code changes required.
- **Step 2 (Pane 2 — M24E–M24H.1):** Verified provisioning block present: `provisioning/*`, `specialization/recipe_runs_storage.py`; CLI `recipe run`, `recipe runs list`, `recipe preview`, `recipe report`, `packs provision`, `value-packs domain-env`; mission_control section `provisioning` (provisioned_packs, recipe_runs_count, failed_count, recommended_next_first_value_flow, missing_prerequisites). No conflicts.
- **Step 3 (Pane 3 — M24F–M24I.1):** Verified rollout block present: `rollout/*` (tracker, demos, launcher, support_bundle, readiness, issues, runbooks); CLI `rollout demos list`, `rollout launch`, `rollout status`, `rollout support-bundle`, `rollout readiness`, `rollout issues report`, `rollout runbooks list/show`; mission_control section `rollout` (rollout_status, target_scenario_id, demo_readiness, next_rollout_action, support_bundle_freshness). No conflicts.

---

## 2. Files with conflicts

**None.** No git conflict markers found. No file was modified by more than one pane in overlapping regions. CLI command groups are additive (capabilities_external ~3452+, recipe_group/recipe_runs ~7568+, rollout_group ~8825+, value_packs_group ~9414+). Mission_control state/report already contained all sections (#18 external_capabilities, #18b activation_executor, #19 value_packs, #20 acceptance, #M24E provisioning, #M24F rollout) from prior integration work.

---

## 3. How each conflict was resolved

N/A — no conflicts. All three blocks were already present and additive. No reconciliation patches were required.

---

## 4. Tests run after each merge

**After full logical integration** (single run covering all three blocks + mission control + runtime mesh):

```bash
cd workflow-llm-dataset
pytest tests/test_capability_activation_block.py tests/test_external_capability.py tests/test_capability_compatibility_m24g1.py tests/test_provisioning.py tests/test_rollout.py tests/test_mission_control.py tests/test_value_packs.py tests/test_acceptance.py -v --tb=short
```

**Result: 89 passed** (6 capability_activation_block, 15 external_capability, 8 capability_compatibility_m24g1, 11 provisioning, 14 rollout, 8 mission_control, 14 value_packs, 10 acceptance).

**Extended slice** (runtime mesh, executor, local_deployment, starter_kits):

```bash
pytest tests/test_runtime_mesh.py tests/test_external_capability_executor.py tests/test_local_deployment.py tests/test_starter_kits.py -v --tb=short
```

**Result: 47 passed** (22 runtime_mesh, 10 external_capability_executor, 6 local_deployment, 9 starter_kits).

**Total: 136 tests passed.** Covers: capability activation (plan, request, execute, list-requests, health), compatibility (matrix, recommend-pack, blocked reasons), domain provisioning (recipe run, packs provision, domain-env), rollout (demos, launch, status, support-bundle, readiness, issues, runbooks), mission control (all sections including activation_executor, provisioning, rollout), value packs, acceptance, runtime mesh, starter kits.

---

## 5. Final integrated command surface

| Group / command | Block | Description |
|-----------------|--------|-------------|
| **capabilities external** | Pane 1 | list, recommend, plan, blocked, explain, **compatibility** [--domain/--value-pack/--tier], **recommend-pack** [--pack/--domain/--field/--tier], request, preview, execute, disable, history, **list-requests** [--status], **health** [--output] |
| **recipe** | Pane 2 | run --id, preview --id, report [--latest]; **recipe runs** list [--limit] |
| **packs** | Pane 2 | **provision** --id [--dry-run] [--no-strict] |
| **value-packs** | Pane 2 + M24B | list, show, recommend, first-run, compare, **domain-env** --id |
| **rollout** | Pane 3 | **demos** list; **launch** --id; **status**; **support-bundle** [--output]; **readiness** [--output]; **issues** report [--output]; **runbooks** list, show \<id\> |
| **acceptance** | M24C | list, run --id, report [--latest] |
| **mission-control** | — | Aggregates external_capabilities, activation_executor, value_packs, provisioning, acceptance, rollout (and others). |

Example usage:

```bash
workflow-dataset capabilities external list
workflow-dataset capabilities external compatibility --value-pack developer_plus
workflow-dataset capabilities external recommend-pack --pack founder_ops_plus --tier local_standard
workflow-dataset capabilities external list-requests --status pending
workflow-dataset capabilities external health
workflow-dataset recipe run --id founder_ops_recipe --dry-run
workflow-dataset packs provision --id founder_ops_plus
workflow-dataset value-packs domain-env --id founder_ops_plus
workflow-dataset rollout demos list
workflow-dataset rollout launch --id founder_demo
workflow-dataset rollout status
workflow-dataset rollout support-bundle
workflow-dataset rollout readiness
workflow-dataset mission-control
```

---

## 6. Remaining risks

- **Trust/cockpit and macros:** Modified files `trust/cockpit.py`, `trust/report.py`, `macros/run_state.py`, `macros/runner.py` were not changed in this integration; if they differ from main, future merges from main may conflict.
- **runtime_mesh:** Modified `runtime_mesh/integration_registry.py`, `runtime_mesh/__init__.py`; mission_control state imports `runtime_mesh.summary`, `validate`, `llama_cpp_check`. All runtime_mesh tests passed.
- **specialization:** `specialization/__init__.py` and recipe_runs_storage; mission_control imports `list_recipe_runs` from specialization. No circular import observed.
- **CLI size:** cli.py is very large; new commands should remain in additive groups to avoid merge churn.
- **Acceptance → value_pack:** Existing risk (acceptance/report imports value_packs.recommend); unchanged by this integration.

---

## 7. Exact recommendation for the next batch

1. **Commit integration state:** Stage and commit the current working tree (or create a single integration commit) so the combined M24D–M24G.1, M24E–M24H.1, M24F–M24I.1 surface is on record.
2. **CI gate:** Add a CI job that runs: `pytest tests/test_capability_activation_block.py tests/test_external_capability.py tests/test_capability_compatibility_m24g1.py tests/test_provisioning.py tests/test_rollout.py tests/test_mission_control.py tests/test_value_packs.py tests/test_acceptance.py tests/test_runtime_mesh.py tests/test_external_capability_executor.py -v --tb=short` (and optionally `workflow-dataset mission-control` and `workflow-dataset rollout launch --id founder_demo` for smoke).
3. **Docs:** Add a short “M24 D/G/H/I integrated surface” section to operator quickstart or deployment doc: capability activation (request → preview → execute), compatibility/recommend-pack, recipe run / packs provision, value-packs domain-env, rollout launch/status/support-bundle/readiness.
4. **No further merge this pane:** No conflict resolution was required. Future work should stay additive; preserve local-first, approval-gated, and inspectable behavior; do not auto-enable downloads or cloud integrations.

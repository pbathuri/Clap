# M49 Integration Pane Report — Pane 1 + 2 + 3

Integration of three completed panes into the `workflow-llm-dataset` project (Clap repo):

- **Pane 1:** M49A–M49D — Portable State Model + Continuity Bundle (what state is portable, bundle create/inspect/validate, profiles, sensitivity policies, report)
- **Pane 2:** M49E–M49H — Migration Validation + Restore/Reconcile Flows (validate bundle for target, dry-run, restore with review, reconcile, verify)
- **Pane 3:** M49I–M49L — Device-Aware Runtime Profiles + Continuity Confidence (device profile, post-restore confidence, downgraded runtime, presets, safe-operating guidance)

Merge order was 1 → 2 → 3 so that portable state (1) is restored safely (2), and device-aware continuity (3) makes restored operation realistic for the target.

---

## 1. Merge steps executed

| Step | Description | Outcome |
|------|-------------|---------|
| **1. Pane 1** | Confirm continuity bundle (create, inspect, validate, components, explain, profiles, sensitivity-policies, report) and mission-control slice. | Already integrated: `continuity_bundle/*`, CLI `continuity-bundle`, mission_control state/report use `continuity_bundle_state`. No git merge; single branch. |
| **2. Pane 2** | Confirm migration restore (validate, dry-run, restore, reconcile, verify, reconcile-policies, playbooks, operator-guidance) and mission-control slice. | Already integrated: `migration_restore/*`, CLI `migration` (validate, dry-run, restore, reconcile, verify, reconcile-policies, playbooks, operator-guidance). mission_control state/report use `migration_restore_state`. |
| **3. Pane 3** | Confirm continuity confidence (status, report, device-profile, explain, device-classes, presets, safe-operating-guidance) and mission-control slice; ensure it uses migration_restore for validation. | Already integrated: `continuity_confidence/*` imports `migration_restore.validation` and `migration_restore.bundle`. CLI `continuity-confidence`, mission_control state/report use `continuity_confidence_state`. |

All three panes were already on the same branch; integration was **validation-only** (no code changes). Dependency order is respected: continuity_bundle (1) → migration_restore (2) → continuity_confidence (3) uses migration_restore.

---

## 2. Files with conflicts

**No merge conflicts** occurred. No files were modified during this integration. Hotspot areas were inspected:

- **`src/workflow_dataset/cli.py`** — Additive command groups only: `continuity-confidence` (earlier in file), `continuity-bundle`, `migration`; no overlapping or conflicting command names.
- **`src/workflow_dataset/mission_control/state.py`** — `continuity_bundle_state`, `migration_restore_state`, `continuity_confidence_state` each populated in separate try/except blocks.
- **`src/workflow_dataset/mission_control/report.py`** — [Continuity bundle], [Migration restore], [Continuity confidence] sections present and non-overlapping; order matches merge order in report flow.
- **memory/*, continuity/*, session/*, queue/*, day/*, install/*, upgrade/*, recovery/*, operator_mode/*, trust/*, approvals/*, audit/** — Not modified by M49 panes; no conflicts introduced.
- **continuity_confidence** depends only on **migration_restore** (validation, bundle manifest); **migration_restore** does not depend on **continuity_bundle** (separate bundle dir/format).

---

## 3. How each conflict was resolved

N/A — no conflicts. Integration consisted of verifying presence, dependency order, tests, and CLI/mission_control wiring.

---

## 4. Tests run after each merge

| After merge | Command | Result |
|-------------|---------|--------|
| Pane 1 | `python3 -m pytest tests/test_continuity_bundle.py -v --tb=line -q` | **25 passed** |
| Pane 2 | `python3 -m pytest tests/test_migration_restore.py -v --tb=line -q` | **14 passed** |
| Pane 3 | `python3 -m pytest tests/test_continuity_confidence.py -v --tb=line -q` | **19 passed** |
| Integration | All three suites run in sequence | **58 passed** total |

---

## 5. Final integrated command surface

M49-relevant top-level groups and subcommands:

| Group | Commands (selected) | Pane |
|-------|---------------------|------|
| **continuity-bundle** | create, inspect, validate, components, explain, profiles, sensitivity-policies, report | 1 |
| **migration** | validate, dry-run, restore, reconcile, verify, reconcile-policies, playbooks, operator-guidance | 2 |
| **continuity-confidence** | status, report, device-profile, explain, device-classes, presets, safe-operating-guidance | 3 |

Mission control report sections (in order): [Continuity bundle] (latest_bundle_id, profile, portable/review_required/excluded/rebuild_only counts, summary), [Migration restore] (latest_bundle, blockers, confidence, next action), … [Continuity confidence] (classification, label, operator_mode_ready, downgraded warnings, next review).

---

## 6. Remaining risks

- **Two bundle systems:** Continuity bundle writes to `data/local/continuity_bundle/bundles/<id>/manifest.json` (M49A–M49D format with components, profile_id). Migration restore reads/writes `data/local/migration_restore/bundles/<id>/manifest.json` (ContinuityBundleManifest with subsystem_ids, paths_in_bundle). There is no automatic bridge: `continuity-bundle create` does not populate migration_restore’s bundle dir, and `migration restore` does not read continuity_bundle manifests. Operators must run migration flows against bundles created in the migration_restore dir (or a future bridge/export step).
- **Restore flow alignment:** For a single “create once, restore anywhere” story, consider: (a) continuity-bundle create → export/copy manifest to migration_restore format or dir, or (b) migration restore accept a path to a continuity_bundle manifest and adapt, or (c) document that “portable state” is defined by continuity-bundle and “restore” is migration_restore with its own manifest source.
- **Device profile and bundle ref:** Continuity confidence uses migration_restore’s `validate_bundle_for_target` and `get_bundle_manifest` (migration_restore bundle dir). Device-aware report is therefore tied to migration_restore bundle refs, not continuity_bundle refs, unless extended later.
- **Mission control full-state test:** Full `get_mission_control_state()` can be slow; consider a fast integration test that builds only M49-related slices and asserts report section presence.
- **Degraded restore visibility:** Continuity confidence exposes downgraded runtime and safe-operating guidance; no change was made to trust/review boundaries. Degraded outcomes remain visible in report/explain.

---

## 7. Exact recommendation for the next batch

1. **Bundle bridge or single source of truth:** Either (a) add a step or CLI that builds a migration_restore bundle from the continuity_bundle manifest (or from the same component set), or (b) allow `migration restore --bundle <path>` to accept a path to a continuity_bundle manifest and convert it for restore, or (c) formally document the two-step flow: “create portable state with continuity-bundle; create restore bundle with migration (or future tool) from same boundaries.”
2. **Mission control CI:** Add a fast test that builds only `continuity_bundle_state`, `migration_restore_state`, `continuity_confidence_state` and asserts structure and that `format_mission_control_report(state)` contains "[Continuity bundle]", "[Migration restore]", "[Continuity confidence]".
3. **Operator runbook:** One short doc: when to use continuity-bundle (create, report, profiles), when to use migration (validate, dry-run, restore), when to use continuity-confidence (status, report, device-profile, presets) after restore or for device-aware planning.
4. **Continuity confidence + continuity_bundle:** Optionally allow continuity confidence report to accept a continuity_bundle bundle ref and map it to a target device profile (e.g. “if I restore this continuity_bundle on this device class, what would confidence be?”) using the same confidence logic, even if the actual restore path still goes through migration_restore.

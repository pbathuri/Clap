# M24 Integration Report — M24A, M24B, M24C

Integration pane: safe merge of External Capability Activation Planner (M24A), Vertical Value Packs (M24B), and First Real-User Acceptance Harness (M24C) in order M24A → M24B → M24C.

---

## 1. Merge steps executed

- **Merge order respected:** Codebase already contained all three workstreams. Integration was additive only; no git merge conflicts (single-branch state).
- **Step 1 (M24A):** Verified M24A surface present: `capabilities external` (list, recommend, plan, blocked, explain), `external_capability/*`, mission_control section #18 `external_capabilities`. No changes required for “merge”; already integrated.
- **Step 2 (M24B):** Verified M24B surface present: `value-packs` (list, show, recommend, first-run, compare), `value_packs/*`. Added mission_control section #19 `value_packs` (recommended pack, missing prereqs count). Added one line to value pack recommendation report: “External capabilities (for this machine/domain): workflow-dataset capabilities external recommend” to wire value packs to the capability layer.
- **Step 3 (M24C):** Verified M24C surface present: `acceptance` (list, run, report), `acceptance/*`. Added mission_control section #20 `acceptance` (scenarios_count, latest_run_*, runs_count). Wired acceptance report to value pack: when formatting an acceptance report, the report now includes “Value pack for this scenario: <value_pack_id>” derived from scenario’s starter_kit_id via `STARTER_KIT_TO_VALUE_PACK`.

---

## 2. Files with conflicts

**None.** No file was modified by more than one pane in overlapping regions. CLI: M24A at ~3451–3530, M24C at ~8579+, M24B at ~9024+ (additive command groups). Mission_control: only M24A had added a section (#18); M24B and M24C had not added mission_control sections before integration.

---

## 3. How each conflict was resolved

N/A — no conflicts. Additive-only integration:

- **mission_control/state.py:** Appended two new try/except blocks (#19 value_packs, #20 acceptance) before `return out`. No existing keys or line ranges were overwritten.
- **value_packs/report.py:** Appended one line to `format_recommendation()` when a pack is present. No existing logic changed.
- **acceptance/report.py:** Added optional resolution of `value_pack_id` from `scenario_id` → `get_scenario` → `starter_kit_id` → `STARTER_KIT_TO_VALUE_PACK`; when present, added two lines to the report before “--- Reasons ---”. No change to existing report structure or semantics.

---

## 4. Tests run after each merge

Single broad slice run after all integration edits (no per-merge runs, as “merges” were additive in one pass):

```bash
pytest tests/test_external_capability.py tests/test_value_packs.py tests/test_acceptance.py tests/test_mission_control.py tests/test_runtime_mesh.py -v --tb=short
```

**Result: 69 passed** (15 external_capability, 14 value_packs, 10 acceptance, 8 mission_control, 22 runtime_mesh).

Covers: runtime mesh / activation planning, value-pack registry / first-value flows, acceptance harness, mission-control / trust / onboarding-related surfaces (starter_kits, environment, report sections).

---

## 5. Final integrated command surface

| Group / command | Source | Description |
|-----------------|--------|-------------|
| **capabilities** | M23D-F1 | scan, report, approvals |
| **capabilities external** | M24A | list, recommend, plan (--source), blocked, explain (--source) |
| **value-packs** | M24B | list, show (--id), recommend, first-run (--id), compare (--id, --id) |
| **acceptance** | M24C | list, run (--id), report [--latest] |
| **approvals** | M23D-F1 | list |
| **runtime** | M23T/M23S | summary, validate, profiles, llama-cpp-check |
| **trust** | M23V | … |
| **onboard** | … | status, bootstrap, approve, … |
| **kits** | M23Y | list, recommend, … |
| **quickstart** | … | … |

Example usage:

```bash
workflow-dataset capabilities external list
workflow-dataset capabilities external recommend --domain founder_ops
workflow-dataset value-packs recommend
workflow-dataset value-packs first-run --id founder_ops_plus
workflow-dataset acceptance run --id founder_first_run
workflow-dataset acceptance report --latest
```

---

## 6. Remaining risks

- **Mission control report UI:** Additive sections were added to `mission_control/report.py` so that `[External capabilities]`, `[Value packs]`, and `[Acceptance]` are rendered when state contains these keys. No remaining risk for report visibility.
- **Acceptance → value_pack import:** `acceptance/report.py` imports `value_packs.recommend.STARTER_KIT_TO_VALUE_PACK`. If value_packs ever imports acceptance, a circular import could appear; currently it does not.
- **Ordering of value_packs vs acceptance in CLI:** M24B (value-packs) is registered after M24C (acceptance) in cli.py. Purely additive; no functional risk.

---

## 7. Exact recommendation for the next batch

1. **Mission control report:** Done. `format_mission_control_report` now includes `[External capabilities]`, `[Value packs]`, and `[Acceptance]` sections.
2. **Optional CI gate:** Add a CI step that runs `workflow-dataset acceptance run --id founder_first_run` (and optionally other scenarios) and treats “partial” or “pass” as success for the integrated surface.
3. **Docs:** Add a short “Integrated M24 surface” section to the quickstart or deployment doc that points to: capabilities external recommend, value-packs recommend / first-run, and acceptance run / report.
4. **No further merge:** No additional conflict resolution required for M24A/M24B/M24C; future work should remain additive to these surfaces and to local-first / approval-gated semantics.

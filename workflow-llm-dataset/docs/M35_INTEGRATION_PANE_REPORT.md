# M35 Integration Pane Report — Authority Tiers, Gates/Audit, Personal Operator Mode

**Date:** 2025-03-16  
**Scope:** Integrate three M35 panes in order: Pane 1 (M35A–M35D + M35D.1) → Pane 3 (M35I–M35L + M35L.1) → Pane 2 (M35E–M35H + M35H.1).

---

## 1. Merge steps executed

| Step | Block | Action |
|------|--------|--------|
| 1 | **Pane 1** (M35A–M35D + M35D.1) | Verified present: `trust/` (tiers, contracts, presets, explain_contract, scope, validation_report, eligibility, cockpit, release_gates). CLI: `trust` group with cockpit, release-gates, readiness-report, **tiers**, **contracts** (list, show, validate), **explain**, **presets** (list, show), eligibility-matrix, validate-config. Mission control: `trust_cockpit`, `authority_contracts_state` and report sections [Trust cockpit], [Authority / Trust contracts]. No code changes. |
| 2 | **Pane 3** (M35I–M35L + M35L.1) | Verified present: `sensitive_gates/` (models, store, flows, summaries). CLI: `gates` (list, show, stage, approve, reject, defer), `audit` (history, project, summary), `trust-review` (pack). Mission control: `sensitive_gates` state and [Gates] report section. No code changes. |
| 3 | **Pane 2** (M35E–M35H + M35H.1) | Verified present: `operator_mode/` (models, store, bundles, pause_revocation, explain). CLI: `operator-mode` (status, bundles, pause, revoke, explain-impact, pause-revocation-report). **Gap:** Mission control did not expose operator mode state. **Fix:** Added `operator_mode_state` block in `state.py` (pause_kind, pause_reason, suspended_*_count, responsibilities_count, bundles_count, next_action, local_sources["operator_mode"]) and [Operator mode] section in `report.py`. |

**Merge order rationale:** Pane 1 defines what high-trust routines are allowed to do; Pane 3 defines review, sign-off, and audit controls; Pane 2 builds personal operator mode on top. All three were already in the same tree; no git merge. The only code change was **adding** mission control visibility for Pane 2 (operator_mode_state + report).

---

## 2. Files with conflicts

There were **no git merge conflicts**. The only functional gap was:

| File | Issue | Resolution |
|------|--------|------------|
| `src/workflow_dataset/mission_control/state.py` | Pane 2 (operator mode) had no state block; mission control could not show pause/revocation/bundles. | Added block **13c. M35E–M35H Personal operator mode**: import load_pause_state, load_suspension_revocation_state, list_responsibility_ids, list_bundle_ids; set `out["operator_mode_state"]` with pause_kind, pause_reason, suspended_responsibility_count, suspended_bundle_count, responsibilities_count, bundles_count, next_action; set `out["local_sources"]["operator_mode"]`. On exception, `out["operator_mode_state"] = {"error": str(e)}`. |
| `src/workflow_dataset/mission_control/report.py` | No report line for operator mode. | Added **[Operator mode]** section: pause=…, suspended_resp=…, suspended_bundles=…, responsibilities=…, bundles=…, next: …. |

---

## 3. How each conflict was resolved

- **state.py:** Additive only. New block uses existing `operator_mode` APIs; no changes to authority_contracts_state or sensitive_gates. Order in state: … authority_contracts_state → **operator_mode_state** → package_readiness …
- **report.py:** Additive only. New section after [Authority / Trust contracts], before [Package readiness].

---

## 4. Tests run after each merge

**Command (from repo root with venv):**
```bash
source .venv/bin/activate
pytest tests/test_trust_authority_contracts.py tests/test_trust_presets_eligibility.py tests/test_trust_cockpit.py tests/test_sensitive_gates.py tests/test_operator_mode.py tests/test_mission_control.py -v --tb=short
```

**Result:** **72 passed** in ~2.1s.

| Suite | Tests | Result |
|-------|--------|--------|
| test_trust_authority_contracts | 13 | All passed (tiers, contracts, validate, scope, explain) |
| test_trust_presets_eligibility | 14 | All passed (presets, eligibility, validate-config) |
| test_trust_cockpit | 8 | All passed (cockpit, release gates, safe_to_expand, readiness) |
| test_sensitive_gates | 15 | All passed (gates, audit, sign-off, ledger, summaries, trust-review pack) |
| test_operator_mode | 12 | All passed (bundles, pause, revoke, explain-impact, report) |
| test_mission_control | 10 | All passed (state structure, report, next-action) |

---

## 5. Final integrated command surface

**Pane 1 — `workflow-dataset trust`**
- `cockpit`, `release-gates`, `readiness-report`
- `tiers` — list authority tiers
- `contracts` — list, show, validate (trusted routine contracts)
- `explain` — explain trust/contract for a routine
- `presets` — list, show (cautious, supervised_operator, bounded_trusted_routine, release_safe)
- `eligibility-matrix`, `validate-config`

**Pane 3 — `workflow-dataset gates`**
- list, show, stage, approve, reject, defer

**Pane 3 — `workflow-dataset audit`**
- history, project, summary (--project / --routine / --tier)

**Pane 3 — `workflow-dataset trust-review`**
- pack [--days 7]

**Pane 2 — `workflow-dataset operator-mode`**
- status, bundles, pause, revoke, explain-impact, pause-revocation-report

**Mission control:** `workflow-dataset mission-control` now includes [Trust cockpit], [Authority / Trust contracts], [Gates], [Operator mode], plus existing sections.

---

## 6. Remaining risks

| Risk | Mitigation |
|------|------------|
| **CLI registration order** | In `cli.py`, `operator-mode` is registered earlier (~1026) than `trust` (~14241) and `gates`/`audit`/`trust-review` (~1537–1738). Logical dependency is Pane 1 → Pane 3 → Pane 2; reordering CLI groups is optional and cosmetic. |
| **Wiring contracts → gates** | Contracts define required_approvals / required_review_gates; gates are a separate layer. Future work: when a routine under a contract triggers a sensitive action, ensure a gate is staged and contract_id is set. |
| **Operator mode ↔ gates** | Pause/revocation affect what work runs; they do not yet explicitly block gate approval or ledger writes. Preserved: no hidden autonomy; operator-mode remains inspectable. |

---

## 7. Recommendation for the next batch

- **Add a test** that `get_mission_control_state(repo_root)` includes `operator_mode_state` with expected keys when operator_mode data dir exists, and that `format_mission_control_report(state)` contains `[Operator mode]` when that state is present.
- **Optional:** Document or reorder CLI so that `trust` and `gates`/`audit`/`trust-review` appear before `operator-mode` in `workflow-dataset --help` if product owner wants the surface to reflect Pane 1 → Pane 3 → Pane 2.
- **Next integration batch:** If adding M35 follow-ons (e.g. contract→gate wiring, operator-mode→gate visibility), keep additive command groups and the same test slice; do not weaken trust/review boundaries.

---

**Summary:** Pane 1 and Pane 3 were already wired in mission control; Pane 2 was missing. Two files changed (mission_control/state.py, mission_control/report.py). All 72 tests in the M35 + mission_control slice pass. No merge conflicts; integration is complete for this batch.

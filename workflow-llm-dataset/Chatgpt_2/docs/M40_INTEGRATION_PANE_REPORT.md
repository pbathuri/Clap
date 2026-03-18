# M40 Integration Pane Report

**Project:** workflow-llm-dataset (Clap repo)  
**Scope:** Integration of three M40 panes — Production Cut, Deployment Bundle, Production Launch  
**Date:** 2026-03-17

---

## 1. Merge steps executed

Integration was **validation-only** (single branch; all three panes already present). No git merge conflicts were resolved. Steps performed:

| Step | Action | Result |
|------|--------|--------|
| 1 | **Pane 1 block (M40A–M40D + M40D.1)** — Verified `production_cut/` present (models, store, lock, freeze, scope_report, production_defaults, quarantine_rules, labels); CLI `production-cut` group; mission_control `production_cut_state`. | OK |
| 2 | **Pane 2 block (M40E–M40H + M40H.1)** — Verified `deploy_bundle/` present (models, store, validation, upgrade_rollback, recovery_report, health, profiles, maintenance_modes); CLI `deploy-bundle` group; mission_control `deploy_bundle_state`. | OK |
| 3 | **Pane 3 block (M40I–M40L + M40L.1)** — Verified `production_launch/` present (gates, decision_pack, runbooks, post_deployment_guidance, review_cycles, sustained_use, ongoing_summary); CLI `production-runbook`, `production-gates`, `launch-decision`; mission_control `production_launch`. | OK |

**Dependency order confirmed:** Pane 1 (production_cut + vertical_selection) → Pane 2 (deploy_bundle, standalone) → Pane 3 (production_launch consumes vertical_selection for scope/gates and checks deploy_bundle dir for gate). No circular imports.

---

## 2. Files with conflicts

**None.** All three panes coexist on one branch. No conflict files were identified. CLI uses additive command groups; mission_control uses distinct state keys (`production_cut_state`, `deploy_bundle_state`, `production_launch`).

---

## 3. How each conflict was resolved

**N/A** — No conflicts. If future branch merges introduce conflicts in the listed hotspots, apply: additive command groups only; preserve local-first / privacy-first / approval-gated / inspectable behavior; do not hide supported/experimental boundaries or weaken trust/review boundaries.

---

## 4. Tests run after each merge

| Pane | Command | Result |
|------|---------|--------|
| Pane 1 | `pytest tests/test_production_cut.py -v --tb=short` | **18 passed** (1.14s) |
| Pane 2 | `pytest tests/test_deploy_bundle.py -v --tb=short` | **11 passed** (0.86s) |
| Pane 3 | `pytest tests/test_production_launch.py -v --tb=short` | **18 passed** (0.86s) |

**Combined M40-relevant tests:** 47 passed.

Mission_control: no dedicated test slice was run for mission_control in this pass; recommend running `pytest tests/test_mission_control.py` in CI for full regression.

---

## 5. Final integrated command surface

All commands are under the main app (e.g. `workflow-dataset`). M40-related groups:

### Pane 1 — Production cut (M40A–M40D + M40D.1)

| Group | Commands |
|-------|----------|
| **production-cut** | `show`, `lock`, `scope`, `explain`, `surfaces`, `production-default`, `quarantine-rules`, `operator-explanations`, `labels` |

### Pane 2 — Deployment bundle (M40E–M40H + M40H.1)

| Group | Commands |
|-------|----------|
| **deploy-bundle** | `show`, `build`, `validate`, `upgrade-path`, `recovery-report`, `profiles`, `profile`, `maintenance-mode` |

### Pane 3 — Production launch (M40I–M40L + M40L.1)

| Group | Commands |
|-------|----------|
| **production-runbook** | `show`, `review-cycle`, `sustained-use`, … |
| **production-gates** | `evaluate` |
| **launch-decision** | `pack`, `explain`, `guidance` |

Additional: `production-readiness` (app-level) aggregates release readiness + production gates + launch decision.

---

## 6. Remaining risks

| Risk | Mitigation |
|------|------------|
| **Production gate surface freeze** | Gate `supported_surface_freeze_complete` uses vertical_selection (active vertical + scope report). It does not yet require an active production_cut; optional follow-up: gate may require active cut and validate against cut’s frozen scope. |
| **Deploy bundle ↔ production cut** | No explicit link between active production cut and deploy_bundle profile (e.g. careful_production_cut). Optional: deploy_bundle profile selection could default or suggest from active cut. |
| **Mission control test suite** | Full `test_mission_control.py` not run in this pass; run in CI for regression. |
| **Docs spread** | Production cut, deployment bundle, and production launch are documented in multiple deliverable docs; consider a single M40 operator/release doc. |

---

## 7. Exact recommendation for the next batch

1. **Wire production cut into surface-freeze gate** — In `production_launch/gates.py`, optionally require active production cut for `supported_surface_freeze_complete` and validate scope against cut’s included/excluded/quarantined (when cut exists).
2. **Optional: deploy_bundle ↔ production cut** — When production cut is locked, suggest or default deploy_bundle profile (e.g. careful_production_cut) and surface in CLI/mission_control.
3. **Run full mission_control test suite** — Execute `pytest tests/test_mission_control.py` in CI and document any failures or skips.
4. **Single M40 operator doc** — Add `docs/M40_OPERATOR_RELEASE_GUIDE.md` (or similar) that links: production-cut lock → scope/surfaces → deploy-bundle build/validate → production-gates evaluate → launch-decision pack → production-runbook, with one-page flow and suggested commands.

---

*End of M40 Integration Pane Report*

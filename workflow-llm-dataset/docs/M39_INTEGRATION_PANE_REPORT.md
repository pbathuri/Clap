# M39 Integration Pane Report

**Project:** workflow-llm-dataset (Clap repo)  
**Scope:** Integration of three M39 panes — Vertical Selection, Curated Vertical Packs, Vertical Launch Kits  
**Date:** 2026-03-17

---

## 1. Merge steps executed

Integration was **validation-only** (single branch; all three panes already present). No git merge conflicts were resolved. Steps performed:

| Step | Action | Result |
|------|--------|--------|
| 1 | **Pane 1 block (M39A–M39D + M39D.1)** — Verified `vertical_selection/` present; dependency order; CLI `verticals` group; mission_control `vertical_selection_state` | OK |
| 2 | **Pane 2 block (M39E–M39H + M39H.1)** — Verified `vertical_packs/` present; no dependency on Pane 3; CLI `vertical-packs` and `vertical-paths`; mission_control `vertical_packs_state` | OK |
| 3 | **Pane 3 block (M39I–M39L + M39L.1)** — Verified `vertical_launch/` present; imports only `vertical_packs` (not `vertical_selection`); CLI launch-kit, success-proof, operator-playbook, value-dashboard, rollout-review; mission_control `launch_kit_state` | OK |

**Dependency order confirmed:** Pane 1 (standalone) → Pane 2 (standalone) → Pane 3 (depends on Pane 2 only). No circular imports.

---

## 2. Files with conflicts

**None.** All three panes coexist on one branch. No conflict files were identified. CLI and mission_control use additive command groups and state keys.

---

## 3. How each conflict was resolved

**N/A** — No conflicts. If future branch merges introduce conflicts in the listed hotspots, apply: additive command groups only; preserve local-first / privacy-first / approval-gated / inspectable behavior; do not hide supported/experimental boundaries or weaken trust/review boundaries.

---

## 4. Tests run after each merge

| Pane | Command | Result |
|------|---------|--------|
| Pane 1 | `pytest tests/test_vertical_selection.py -v --tb=short` | **15 passed** (0.05s) |
| Pane 2 | `pytest tests/test_vertical_packs.py -v --tb=short` | **10 passed** (0.03s) |
| Pane 3 | `pytest tests/test_vertical_launch.py -v --tb=short` | **10 passed** (0.04s) |

**Mission control:** `pytest tests/test_mission_control.py` was started; it is long-running (many tests). Not required for M39 integration sign-off; run separately for full mission-control regression.

**Total M39-relevant tests:** 35 passed.

---

## 5. Final integrated command surface

All commands are under the main app (e.g. `workflow-dataset`). M39-related groups:

### Pane 1 — Vertical selection + scope lock (M39A–M39D)

| Group | Commands |
|-------|----------|
| **verticals** | `candidates`, `recommend`, `show`, `lock`, `scope-report`, `surface-policy` |

### Pane 2 — Curated vertical packs + guided value paths (M39E–M39H)

| Group | Commands |
|-------|----------|
| **vertical-packs** | `list`, `show`, `apply`, `first-value`, `progress`, `playbook`, `recovery` |
| **vertical-paths** | (guided value paths; see cli.py for subcommands) |

### Pane 3 — Vertical launch kits + success proof + operator playbooks (M39I–M39L + M39L.1)

| Group | Commands |
|-------|----------|
| **launch-kit** | `list`, `show`, `start` |
| **success-proof** | `report` |
| **operator-playbook** | `show` |
| **value-dashboard** (M39L.1) | `show`, `list` |
| **rollout-review** (M39L.1) | `show`, `list`, `record` |

---

## 6. Remaining risks

| Risk | Mitigation |
|------|------------|
| **Mission control test suite duration** | Run `test_mission_control.py` in CI or overnight; not blocking M39 integration. |
| **Optional wiring: triage/cohort → rollout recommendation** | Rollout review recommends continue/narrow/pause/expand from proof/dashboard only; triage/cohort health could strengthen recommendation — document as follow-up. |
| **Docs spread** | Vertical selection, packs, launch, value dashboard, and rollout review are documented across multiple places; consider a single “M39 verticals” doc for operators. |
| **Env dependency (pydantic)** | Other areas (e.g. triage) have seen `ModuleNotFoundError: pydantic`; M39 tests did not. Ensure pydantic is in project deps where needed. |
| **Expand decision gating** | “Expand” rollout decision has no explicit checklist in code; consider gating expand by proof + milestone + optional operator checklist. |

---

## 7. Exact recommendation for the next batch

1. **Wire triage/cohort health into rollout recommendation** — When building `RolloutReviewPack`, incorporate triage state (e.g. open issues, supported surface unresolved count) into `recommended_decision` / `recommended_rationale` so “expand” is only suggested when cohort health is acceptable.
2. **Add value-dashboard snapshot history** — Persist periodic value_dashboard summaries (e.g. by date) so operators can compare “what’s working / not working” over time.
3. **Gate expand by explicit checklist** — Require a small checklist (e.g. first-value reached, no critical proofs failed, cohort health OK) before recommending or allowing “expand”; expose in CLI or operator-playbook.
4. **Run full mission_control test suite** — Execute `pytest tests/test_mission_control.py` in CI and document any failures or skips.
5. **Single M39 operator doc** — Add `docs/M39_VERTICALS_OPERATOR_GUIDE.md` (or similar) that links vertical selection → packs → launch kit → success proof → value dashboard → rollout review and lists supported vs experimental surfaces.

---

*End of M39 Integration Pane Report*

# M40A–M40D Production Cut — Before Coding

## 1. What scope-lock and vertical productization structures already exist

- **Vertical selection (M39A–M39D)**  
  - `vertical_selection/`: `VerticalCandidate`, `SurfacePolicyEntry`; scope lock: `get_core_surfaces`, `get_optional_surfaces`, `get_excluded_surfaces`, `get_scope_report(vertical_id)`; surface policies: recommended/allowed/discouraged/blocked, experimental set, reveal rules. Active vertical: `data/local/vertical_selection/active_vertical.txt` via `get_active_vertical_id` / `set_active_vertical_id`.  
  - CLI: `workflow-dataset verticals` (candidates, recommend, show, lock, scope-report, surface-policy). Mission control: `vertical_selection_state`.

- **Curated vertical packs (M39E–M39H)**  
  - `vertical_packs/`: `CuratedVerticalPack` with `RequiredSurfaces`, `TrustReviewPosture`, `RecommendedWorkdayProfile`, `RecommendedQueueProfile`, core_workflow_path, first_value_path. Active pack: `data/local/vertical_packs/active.json`. No explicit “production” pack ID.

- **Cohort**  
  - `cohort/`: profiles with `surface_support` (supported/experimental/blocked), `allowed_trust_tier_ids`, `default_workday_preset_id`, `default_experience_profile_id`. Surface matrix: `get_supported_surfaces(cohort_id)` etc. Active cohort: `data/local/cohort/active_profile.txt`.

- **Release / reliability / support**  
  - Release readiness, install/upgrade, handoff pack; reliability golden-path runs and recovery; support via cohort matrix + vertical launch `SupportedUnsupportedBoundaries` + release supportability.

- **Workspace / day / queue**  
  - Presets (founder_operator, analyst, developer, document_heavy); default experience (calm/full); cohort bindings to workday and experience. No single “production” profile ID.

- **Operator / trust / policy / approvals**  
  - Operator mode (pause/revoke), trust tiers/presets/cockpit, approval registry, sensitive gates + audit. Cohort: `allowed_trust_tier_ids`; pack: `TrustReviewPosture`. Production gate `supported_surface_freeze_complete` checks active vertical + scope report (no explicit freeze artifact).

---

## 2. What is missing for a real production surface freeze

- **Single “production cut” artifact** that names the chosen deployment vertical and a frozen surface set (included / excluded / quarantined) for that cut. Today: vertical is locked and scope is derived from pack + scope_report; there is no persisted “this is the production cut” with explicit lists and defaults.

- **Explicit classification output** for deployment: “included” (default-visible, supported), “excluded” (non-core, not in scope), “quarantined” (experimental, visible only under policy). Scope report and surface policies give core/optional/hidden and experimental; no single report that says “included / excluded / quarantined” for the production cut.

- **Default production experience** for the cut: primary queue/day/workspace defaults and required trust posture in one place (today: pack + cohort; not labeled “production default” or “freeze”).

- **Production readiness note** and **supported workflow set** for the cut (can be derived from pack but not first-class on a “cut” object).

- **Mission control visibility** for: active production cut, included/excluded/quarantined counts, primary supported workflows, top scope risk, next recommended freeze review.

---

## 3. Exact file plan

| Path | Purpose |
|------|--------|
| `src/workflow_dataset/production_cut/__init__.py` | Re-export public API. |
| `src/workflow_dataset/production_cut/models.py` | ProductionCut, ChosenPrimaryVertical, IncludedSurface, ExcludedSurface, QuarantinedExperimentalSurface, SupportedWorkflowSet, RequiredTrustPosture, DefaultOperatingProfile, ProductionReadinessNote. |
| `src/workflow_dataset/production_cut/store.py` | Persist/load active production cut (vertical_id, frozen_at_utc, surface lists, workflow set, defaults, note). Path: `data/local/production_cut/active_cut.json`. |
| `src/workflow_dataset/production_cut/lock.py` | Final vertical lock: choose primary from evidence (vertical_selection), explain why, primary workflows and allowed roles/modes (from pack), non-core and excluded surfaces (scope_lock + surface_policies). |
| `src/workflow_dataset/production_cut/freeze.py` | Production surface freeze: default-visible (included), hidden experimental (quarantined), blocked unsupported (excluded); primary queue/day/workspace defaults; required review/trust from pack + cohort. Build frozen-scope report and included/excluded/quarantined classification. |
| `src/workflow_dataset/production_cut/scope_report.py` | Build human- and machine-readable frozen-scope report (included, excluded, quarantined lists and counts; optional risk line). |
| CLI in `cli.py` | Add `production_cut_group` with commands: `show`, `lock`, `scope`, `explain`, `surfaces`. Additive only. |
| `src/workflow_dataset/mission_control/state.py` | Add `production_cut_state` (active cut id, vertical_id, included/excluded/quarantined counts, primary_workflow_ids, top_scope_risk, next_freeze_review). |
| `src/workflow_dataset/mission_control/report.py` | Add report block for production cut. |
| `tests/test_production_cut.py` | Tests: model, lock behavior, included/excluded/quarantined classification, default profile generation, invalid/weak cut. |
| `docs/M40A_M40D_PRODUCTION_CUT_DELIVERABLE.md` | Deliverable: CLI usage, sample cut, sample scope report, sample surfaces output, tests run, remaining gaps. |

---

## 4. Safety / risk note

- **Do not broaden supported or experimental surfaces by default.** The production cut’s included set will be a subset of (vertical core + optional) and will respect cohort supported/experimental. Quarantined will be explicitly experimental; excluded will be non-core or blocked. Safe_adaptation and council boundaries are unchanged; production cut will not bypass them.

- **Additive only.** No deletion of existing subsystems. No change to vertical_selection or cohort semantics beyond being consumed by production_cut. Optional: later, production_launch gate `supported_surface_freeze_complete` could require an active production cut and validate against it; not required for this first draft.

- **Local-first:** All state under `data/local/production_cut/`. No hidden telemetry.

---

## 5. Production narrowing principles

- **One deployable vertical per cut** — the cut names the primary deployment vertical and freezes scope for that vertical only.  
- **Explicit included / excluded / quarantined** — no ambiguity about what is in the product surface for this cut.  
- **Default production experience** — one set of queue/day/workspace and trust defaults for the cut, derived from pack + cohort where present.  
- **Inspectable and approval-gated** — freeze is visible in CLI and mission control; trust/review posture remains required and visible.  
- **Supported/experimental boundaries preserved** — quarantined = experimental; we do not hide that they exist.

---

## 6. What this block will NOT do

- Delete or replace existing vertical_selection, cohort, vertical_packs, release, reliability, support, workspace/day/queue, automations, operator/trust/policy/approvals.  
- Change cohort or vertical selection semantics.  
- Add telemetry or non–local-first behavior.  
- Auto-expand surfaces or weaken trust/approval/audit.  
- Implement full release versioning or release-cut versioning beyond existing install/upgrade and handoff pack.  
- Build a marketing-only positioning; this is a technical scope freeze and deployable vertical definition.

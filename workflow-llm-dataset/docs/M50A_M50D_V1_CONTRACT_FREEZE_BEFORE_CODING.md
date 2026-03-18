# M50A–M50D — v1 Contract Freeze + Surface Finalization: Before Coding

## 1. What the current production cut already includes

- **production_cut/models.py:** ProductionCut (cut_id, vertical_id, frozen_at_utc, chosen_vertical, included_surface_ids, excluded_surface_ids, quarantined_surface_ids, supported_workflows, required_trust, default_profile, production_readiness_note). ChosenPrimaryVertical (vertical_id, primary_workflow_ids, allowed_roles, allowed_modes, non_core_surface_ids, excluded_surface_ids). IncludedSurface, ExcludedSurface, QuarantinedExperimentalSurface. SupportedWorkflowSet, RequiredTrustPosture, DefaultOperatingProfile, ProductionReadinessNote. ProductionDefaultProfile, ExperimentalQuarantineRule, ProductionSafeLabel.
- **production_cut/freeze.py:** build_production_freeze(vertical_id) → included_surface_ids, excluded_surface_ids, quarantined_surface_ids (from vertical_selection scope_lock + surface_policies).
- **production_cut/scope_report.py:** build_frozen_scope_report(cut | vertical_id), build_surfaces_classification (included/excluded/quarantined with labels).
- **production_cut/store.py:** get_active_cut(), set_active_cut(); active cut in data/local/production_cut/active_cut.json.
- **production_cut/lock.py:** Lock production cut (freeze at a point in time).
- **stable_v1_gate:** FinalEvidenceBundle (v1_contract_summary string, production_cut_frozen, production_cut_vertical_id, …), evaluate_stable_v1_gate(evidence), StableV1Decision, StableV1Report.
- **v1_ops:** V1SupportPosture, build_v1_support_posture(), maintenance pack, runbook.

So: vertical lock, included/excluded/quarantined surfaces, supported workflows, required trust, default profile, and readiness note exist. Stable-v1 gate evaluates evidence and produces a recommendation; v1_ops aggregates support posture and maintenance.

## 2. What remains ambiguous for a true stable v1 contract

- **Single canonical v1 contract document** — No first-class StableV1Contract that is *the* product contract: what is v1 core, v1 advanced (supported), quarantined, excluded, with one place to read and report.
- **Explicit v1 core vs v1 advanced** — Production cut has “included” (default-visible) and “quarantined”; it does not separate “v1 core” (must work, fully supported) from “v1 advanced” (supported but optional or power-user). Labels/production_safe exist but are not wired into a contract view.
- **Stable workflow contract** — SupportedWorkflowSet on ProductionCut exists; no dedicated “stable workflow contract” report (which workflows are in v1, which are excluded, and why).
- **Support commitment note** — ProductionReadinessNote has summary/blockers/warnings; no explicit “support commitment” (what we promise for v1, what we do not).
- **Explain-by-surface** — No single explain(surface_id) that returns “v1_core | v1_advanced | quarantined | excluded” and rationale for operators/users.
- **Freeze report** — No single “v1 freeze report” that summarizes: what is in v1, what is excluded, what is quarantined, what users may rely on, and next recommended freeze action.
- **Mission control** — No slice that surfaces “active v1 contract,” “quarantined experimental,” “excluded,” “top v1 ambiguity,” “next freeze action.”

## 3. Exact file plan

| Item | Path | Purpose |
|------|------|--------|
| Models | `src/workflow_dataset/v1_contract/models.py` | StableV1Contract, V1CoreSurface, V1SupportedAdvancedSurface, QuarantinedExperimentalSurface, ExcludedSurface, StableWorkflowContract, SupportedOperatingPosture, SupportCommitmentNote. |
| Build | `src/workflow_dataset/v1_contract/contract.py` | build_stable_v1_contract(repo_root) from get_active_cut + build_production_freeze; classify core vs advanced; return StableV1Contract. |
| Surfaces | `src/workflow_dataset/v1_contract/surfaces.py` | get_v1_surfaces_classification(contract), list_v1_core(), list_quarantined(), list_excluded(). |
| Workflows | `src/workflow_dataset/v1_contract/workflows.py` | get_stable_workflow_contract(contract) → workflow list with in/out and rationale. |
| Explain | `src/workflow_dataset/v1_contract/explain.py` | explain_surface(surface_id, contract) → classification, rationale, may_rely_on. |
| Report | `src/workflow_dataset/v1_contract/report.py` | build_freeze_report(contract) → what is in v1, excluded, quarantined, may_rely_on, next_freeze_action. |
| Mission control | `src/workflow_dataset/v1_contract/mission_control.py` | v1_contract_slice(repo_root). |
| CLI | `src/workflow_dataset/cli.py` | v1_contract_group: show, surfaces, workflows, explain --surface, freeze-report. |
| Mission control state/report | `mission_control/state.py`, `mission_control/report.py` | Add v1_contract_state and “[V1 contract]” section. |
| Tests | `tests/test_v1_contract.py` | Contract build, surface classification, workflows, explain, freeze-report, mission control. |
| Doc | `docs/M50A_M50D_V1_CONTRACT_FREEZE_DELIVERABLE.md` | Files, CLI, samples, tests, gaps. |

## 4. Safety/risk note

- **Do not replace production_cut or stable_v1_gate** — v1_contract reads from them and presents a unified contract view; it does not change how cut or gate work.
- **Do not hide quarantined or excluded** — Quarantined and excluded surfaces must remain visible and explained; no softening of scope.
- **Do not promise support we do not have** — Support commitment note must be explicit and conservative; operators must see what is in/out of v1.

## 5. v1-freeze principles

- **One contract** — A single StableV1Contract is the source of truth for what stable v1 is.
- **Explicit classification** — Every major surface is v1_core, v1_advanced, quarantined, or excluded, with a reason.
- **Inspectable** — Contract, surfaces, workflows, and explain are available via CLI and mission control.
- **Sustained use** — Contract supports “what can users/operators rely on” without roadmap sprawl.

## 6. What this block will NOT do

- Redesign production_cut, stable_v1_gate, or v1_ops.
- Open new verticals or expand scope.
- Delete or hide history or prior systems.
- Add cloud or multi-tenant contract variants.

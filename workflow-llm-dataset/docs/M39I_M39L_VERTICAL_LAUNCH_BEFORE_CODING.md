# M39I–M39L — Vertical Launch Kits + Success Proof + Operator Playbooks (Before Coding)

## 1. What launch/readiness/support surfaces already exist

- **vertical_selection (Pane 1):** VerticalCandidate, SurfacePolicyEntry, scope lock, store; mission_control vertical_selection_state (recommended primary/secondary, active_vertical_id, surfaces_hidden_by_scope).
- **vertical_packs (Pane 2):** CuratedVerticalPack, FirstValuePath, SuccessMilestone, FirstValuePathStep, CommonFailurePoint, VerticalPlaybook, RecoveryPath, VerticalPlaybookFailureEntry; paths.build_path_for_pack; progress.get_next_vertical_milestone, get_blocked_vertical_onboarding_step, build_milestone_progress_output; playbooks.get_playbook_for_vertical, get_operator_guidance_when_stalled; store (get_active_pack, set_active_pack, get_path_progress, set_milestone_reached); registry (get_curated_pack, built-in packs); mission_control vertical_packs_state (active_curated_pack_id, path_id, next_milestone, reached_milestone_ids, blocked_onboarding_step, operator_guidance_when_stalled).
- **onboarding:** get_onboarding_status (profile, env_ready, capabilities, approval_summary, blocked_or_unavailable, recommended_next_steps); bootstrap_profile; approval_bootstrap.
- **release:** get_dashboard_data (readiness, cohort, review_package, next_actions); reporting_workspaces; review_state.
- **operator_quickstart:** build_first_value_flow (steps: bootstrap, runtime, onboard approvals, jobs list, inbox); first_run_tour; quick_reference; status_card.
- **reliability/support:** Existing harnesses and support modules; no single “launch kit” or “success proof” aggregation.

**Summary:** Vertical scope (Pane 1) and curated packs + first-value paths + vertical playbooks (Pane 2) exist. Onboarding, release readiness, and operator quickstart exist. **Missing:** a single **launch kit** that packages one vertical into a launchable unit with explicit setup checklist, **success proof** metrics (first useful artifact, first review cycle, first continuity, first trusted routine, reduced overhead, successful recovery), **operator playbook** as first-class launch support, and **launch blockers** / **next operator action** visibility.

---

## 2. What is missing for a true vertical launch and success-proof layer

- **Vertical launch kit model:** One unit per vertical that ties: curated_pack_id, vertical_id (scope), first-run launch path, required setup checklist (env, approvals, surfaces), success proof metrics, first-value checkpoint, operator support playbook, supported/unsupported boundaries, recovery/escalation guidance.
- **Explicit success proof metrics:** Track and report: first useful artifact, first review/approval cycle, first continuity/resume success, first recurring routine trusted, reduction in blocked/manual overhead, successful recovery from common failure. Tied to vertical + cohort + supported workflow path.
- **Required setup checklist:** Gates for “launch start” (env ready, approvals minimal, surfaces available); stored and visible so operator knows what’s blocking launch.
- **Launch kit start flow:** Start a launch (set active pack, apply scope if needed, record launch_started_at) so time-to-first-value and proof state can be measured.
- **Success-proof report:** Per launch kit (or active launch): which proofs are met, which pending/failed; cohort and path context.
- **Operator playbook as launch support:** Single entry (e.g. operator-playbook show --id founder_operator_launch) that surfaces setup, first-value coaching, common recovery, when to narrow scope, when to escalate/downgrade cohort, how to review trust/operator posture.
- **Mission control:** Active launch kit, first-value progress, proof-of-value status, launch blockers, next operator support action.

---

## 3. Exact file plan

| Area | Action | Path |
|------|--------|------|
| Models | Create | `src/workflow_dataset/vertical_launch/models.py` — VerticalLaunchKit, FirstRunLaunchPath, RequiredSetupChecklist, SuccessProofMetric, FirstValueCheckpoint, OperatorSupportPlaybook (launch wrapper), SupportedUnsupportedBoundaries, RecoveryEscalationGuidance |
| Success proof | Create | `src/workflow_dataset/vertical_launch/success_proof.py` — proof types, record_proof, list_proofs, build_success_proof_report |
| Store | Create | `src/workflow_dataset/vertical_launch/store.py` — active launch kit, launch_started_at, setup_checklist_state, proof_state; get/set |
| Kits | Create | `src/workflow_dataset/vertical_launch/kits.py` — build_launch_kit_for_vertical (from curated pack + vertical_selection + playbook), list_launch_kits |
| CLI | Create | `src/workflow_dataset/vertical_launch/cli.py` or add to cli.py: launch-kit list/show/start; success-proof report; operator-playbook show |
| Mission control | Modify | `src/workflow_dataset/mission_control/state.py` — launch_kit_state: active_launch_kit_id, first_value_progress, proof_of_value_status, launch_blockers, next_operator_support_action |
| Mission control report | Modify | `src/workflow_dataset/mission_control/report.py` — [Vertical launch] section |
| Init | Create | `src/workflow_dataset/vertical_launch/__init__.py` |
| Tests | Create | `tests/test_vertical_launch.py` |
| Docs | Create | `docs/M39I_M39L_VERTICAL_LAUNCH_DELIVERABLE.md` |

---

## 4. Safety/risk note

- **Narrow scope:** Launch kits only for verticals that already have a curated pack and scope lock; no automatic expansion of supported surfaces.
- **No hidden telemetry:** Success proof and launch state are local-only; no silent reporting.
- **Inspectable:** Setup checklist and proof state are visible in CLI and mission control; failed first-value attempts are not hidden.
- **Trust/review unchanged:** Operator playbooks advise; they do not bypass approval or trust boundaries.

---

## 5. Success-proof principles

1. **Measurable:** Each proof is a concrete event or condition (e.g. first_run_completed, first_simulate_done, first_real_done, first_continuity_resume, first_trusted_routine).
2. **Tied to vertical and path:** Proofs are scoped to the active launch kit and its first-value path.
3. **Reportable:** Success-proof report shows met / pending / failed per proof type.
4. **Recovery counts:** Successful recovery from a common failure is itself a proof (product helped user recover).
5. **No vague value:** Avoid “user felt productive”; use milestones and proofs that the product actually delivered an outcome.

---

## 6. What this block will NOT do

- **No** broadening of vertical scope beyond existing curated packs and vertical_selection.
- **No** rebuild of onboarding, release, support, or vertical_packs from scratch; integration via existing APIs.
- **No** vague value claims; value is measured via proofs and milestones.
- **No** hiding of failed first-value attempts; blockers and stalled state are visible.
- **No** SaaS customer-success tooling; local-first, operator-controlled only.

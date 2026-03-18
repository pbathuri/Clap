# M40I–M40L Production Runbooks + Release Gates + Launch Decision Pack — Before Coding

## 1. What launch/readiness/runbook structures already exist

- **Release readiness** (`release_readiness/`): ReleaseReadinessStatus (ready|blocked|degraded), ReleaseBlocker, ReleaseWarning, SupportedWorkflowScope, KnownLimitation, SupportabilityStatus; build_release_readiness() from rollout, package_readiness, env, acceptance. Mission control reports [Release readiness].
- **Rollout gates** (`release_readiness/gates.py`): RolloutGate, GATES (env_required_ok, acceptance_pass, first_user_ready, release_readiness_not_blocked, rollout_stage_ready, trust_approval_ready); evaluate_gate(gate_id, repo_root).
- **Launch profiles** (`release_readiness/models.py`, profiles): LaunchProfile (profile_id, required_gate_ids) — demo, internal pilot, careful first user, etc.
- **Cohort gates** (`cohort/gates.py`): ReadinessGate, evaluate_gates(cohort_id) — release_not_blocked, no_critical_triage, no_downgrade_recommended, reliability_pass_or_na.
- **Triage playbooks** (`triage/playbooks.py`): MitigationPlaybook, OperatorDoNow, get_default_playbooks(), get_playbook(id), get_operator_do_now_for_cluster() — executor_blocked, install_upgrade, etc.; links to support/recovery/readiness.
- **Vertical playbooks** (`vertical_packs/playbooks.py`): VerticalPlaybook (failure_entries, recovery_paths, operator_guidance_stalled); get_playbook_for_vertical(id).
- **Vertical selection** (`vertical_selection/`): active_vertical_id, get_scope_report(), get_surface_policy_report(); recommended primary/secondary.
- **Mission control**: Aggregates release_readiness, cohort_state, vertical_selection_state, triage, etc. No single “launch decision recommendation” or “production runbook” block.

## 2. What is missing for a true production decision pack

- **Production runbook model**: No single “production runbook” type that ties together operating checklist, daily operating review, recovery path, support path, trusted routine review step for the chosen vertical. Vertical playbooks exist but are failure/recovery; no explicit “daily ops” or “pre-launch checklist.”
- **Launch gate vs rollout gate**: Rollout gates are generic; no production-specific gates such as “supported surface freeze complete,” “deployment bundle valid,” “chosen vertical first-value proof acceptable” in one evaluated set.
- **Launch decision pack**: No assembled artifact that combines chosen vertical, supported scope, gate results, open blockers/warnings, recovery/trust/support posture, and a **recommended decision** (launch | launch_narrowly | pause | repair_and_review). Release readiness has status + blockers but no explicit “launch decision” or “no-launch/rollback” recommendation.
- **Launch blocker vs warning**: ReleaseBlocker/ReleaseWarning exist in release_readiness; no separate “launch blocker” / “launch warning” that can aggregate from multiple sources (readiness, cohort gates, vertical, deployment bundle) for the decision pack.
- **Inspectable decision**: No CLI or report that shows “why launch” or “why pause” with failed gates and highest-severity blocker. No “launch-decision explain.”
- **Mission control**: No block for “current launch decision recommendation,” “failed release gates,” “highest-severity blocker,” “support readiness,” “next required launch-review action.”

## 3. Exact file plan

| Action | Path | Purpose |
|--------|------|--------|
| Create | `src/workflow_dataset/production_launch/__init__.py` | Exports |
| Create | `src/workflow_dataset/production_launch/models.py` | ProductionRunbook, OperatingChecklistItem, LaunchGate, LaunchBlocker, LaunchWarning, LaunchDecision (launch/launch_narrowly/pause/repair_and_review), TrustedRoutineReviewStep |
| Create | `src/workflow_dataset/production_launch/runbooks.py` | get_production_runbook(vertical_id): operating checklist, daily review steps, recovery path ref, support path ref, trusted routine review steps (from vertical playbook + static) |
| Create | `src/workflow_dataset/production_launch/gates.py` | PRODUCTION_GATE_* ids; evaluate_production_gates(repo_root) -> list of {gate_id, passed, detail}; uses release_readiness, cohort gates, vertical scope, optional deployment bundle check |
| Create | `src/workflow_dataset/production_launch/decision_pack.py` | build_launch_decision_pack(repo_root): chosen vertical, supported scope, gate results, blockers, warnings, recovery/trust/support posture, recommended_decision, explain string |
| Modify | `src/workflow_dataset/cli.py` | production_runbook_group: production-runbook show; production_gates_group: production-gates evaluate; launch_decision_group: launch-decision-pack, launch-decision explain; production-readiness (alias or aggregate) |
| Modify | `src/workflow_dataset/mission_control/state.py` | production_launch_state: recommended_decision, failed_gates, highest_blocker, support_readiness, next_launch_review_action |
| Modify | `src/workflow_dataset/mission_control/report.py` | [Production launch] section |
| Create | `tests/test_production_launch.py` | Runbook, gates evaluation, decision pack generation, blocker/warning, no-launch/pause/repair cases, incomplete state |
| Create | `docs/M40I_M40L_PRODUCTION_LAUNCH_AND_DECISION_PACK.md` | Files, CLI, samples, tests, gaps |

## 4. Safety/risk note

- **Evidence-based**: Launch decision is derived from actual gate results and blockers; no subjective “we think it’s ready.” Failed gates surface as failed; blockers are not softened.
- **No hiding**: Blockers and failed gates are visible in the pack and in mission control. “Pause” or “repair_and_review” are first-class outcomes.
- **Local-first**: All inputs are from local state (readiness, cohort, vertical, triage, reliability). No cloud release orchestration or enterprise change-management dependency.
- **Runbook as reference**: Production runbook is advisory; it does not auto-execute steps. Operators use it for daily ops and escalation.

## 5. Launch-discipline principles

- **Gates must pass for launch**: At least release_readiness not blocked and (when cohort/vertical set) cohort gates and vertical scope consistent. Additional production gates (bundle valid, first-value proof) can be added.
- **Blockers block launch**: Any launch blocker → recommended decision pause or repair_and_review. Warnings reduce to launch_narrowly or add to explain.
- **Recovery and support paths explicit**: Decision pack includes recovery posture and support posture so operators know where to go post-release.
- **Decision is inspectable**: explain_launch_decision() returns why launch / why pause / what to fix.

## 6. What this block will NOT do

- Will not rebuild release_readiness, cohort gates, or vertical selection; only consume and aggregate.
- Will not add cloud release or deployment orchestration; deployment bundle “valid” can be a local path or manifest check if present.
- Will not auto-approve or auto-ship; the pack is an artifact for human/operator decision.
- Will not hide or soften blockers; failed gates and blockers are reported as-is.

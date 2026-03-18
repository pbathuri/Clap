# M39I–M39L — Vertical Launch Kits + Success Proof + Operator Playbooks (Deliverable)

First-draft vertical launch layer: package each vertical into a launch kit, define success-proof metrics, operator playbooks, and mission-control visibility. Local-first; no hidden telemetry.

---

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/cli.py` | Added **launch-kit** group: `list`, `show --id`, `start --id`. Added **success-proof** group: `report --id`. Added **operator-playbook** group: `show --id`. |
| `src/workflow_dataset/mission_control/state.py` | Added **launch_kit_state**: active_launch_kit_id, launch_started_at_utc, first_value_progress_*, proof_of_value_met_count/pending_count, first_value_milestone_reached, launch_blockers, next_operator_support_action, suggested_success_proof_report. |
| `src/workflow_dataset/mission_control/report.py` | Added **[Vertical launch]** section: active_launch_kit, proof_met/pending, first_value_milestone_reached, launch_blockers, next_operator_action, suggested command. |

## 2. Files created

| File | Purpose |
|------|---------|
| `src/workflow_dataset/vertical_launch/__init__.py` | Package exports. |
| `src/workflow_dataset/vertical_launch/models.py` | VerticalLaunchKit, FirstRunLaunchPath, RequiredSetupChecklist, SuccessProofMetric, FirstValueCheckpoint, OperatorSupportPlaybook, SupportedUnsupportedBoundaries, RecoveryEscalationGuidance. |
| `src/workflow_dataset/vertical_launch/store.py` | get/set active_launch, get/set proof_state, record_proof_met. |
| `src/workflow_dataset/vertical_launch/success_proof.py` | Proof types, get_proof_metrics_for_kit, build_success_proof_report. |
| `src/workflow_dataset/vertical_launch/kits.py` | build_launch_kit_for_vertical, list_launch_kits (from curated packs + playbooks). |
| `docs/M39I_M39L_VERTICAL_LAUNCH_BEFORE_CODING.md` | Before-coding: existing/missing, file plan, safety, success-proof principles. |
| `docs/M39I_M39L_VERTICAL_LAUNCH_DELIVERABLE.md` | This deliverable. |
| `tests/test_vertical_launch.py` | Tests: list kits, build kit, active launch, proof state/report, record_proof_met, operator playbook, boundaries. |

---

## 3. Exact CLI usage

```bash
# List vertical launch kits
workflow-dataset launch-kit list [--json]

# Show one launch kit
workflow-dataset launch-kit show --id founder_operator_launch [--json]
workflow-dataset launch-kit show --id founder_operator_core [--json]

# Start a vertical launch (set active launch kit + active pack; record launch_started_at)
workflow-dataset launch-kit start --id founder_operator_launch [--repo PATH] [--json]

# Success-proof report for a launch kit
workflow-dataset success-proof report --id founder_operator_launch [--cohort ID] [--repo PATH] [--json]

# Operator playbook for a launch kit
workflow-dataset operator-playbook show --id founder_operator_launch [--json]
```

---

## 4. Sample launch kit

Built from `founder_operator_core` curated pack:

```json
{
  "launch_kit_id": "founder_operator_core_launch",
  "vertical_id": "founder_operator_core",
  "curated_pack_id": "founder_operator_core",
  "label": "Founder / Operator (core) launch",
  "description": "Curated pack for founders and small-team operators...",
  "first_run_path": {
    "path_id": "founder_ops_plus_first_value",
    "label": "Founder ops first value",
    "entry_point": "workflow-dataset package first-run",
    "step_titles": ["...", "..."],
    "required_surface_ids": ["workspace_home", "queue_summary", "approvals_urgent", "continuity_carry_forward"],
    "first_value_milestone_id": "first_simulate_done"
  },
  "required_setup": {
    "checklist_id": "founder_operator_core_setup",
    "items": [
      {"id": "env_ready", "label": "Environment ready", "blocking": true, "command_hint": "workflow-dataset package first-run"},
      {"id": "approvals_minimal", "label": "Approvals minimal", "blocking": true, "command_hint": "workflow-dataset onboard status"},
      {"id": "surfaces_available", "label": "Surfaces available", "blocking": false, "command_hint": "workflow-dataset vertical-packs first-value --id founder_operator_core"}
    ]
  },
  "success_proof_metrics": [...],
  "operator_playbook": { "playbook_id": "founder_operator_playbook", "setup_guidance": "...", "first_value_coaching": "...", ... },
  "supported_unsupported": { "supported_surface_ids": [...], "supported_workflow_ids": ["morning_ops", "weekly_status_from_notes", ...] },
  "recovery_escalation": [...]
}
```

---

## 5. Sample success-proof report

```bash
workflow-dataset success-proof report --id founder_operator_core_launch
```

Example output:

```
Success-proof report  launch_kit=founder_operator_core_launch  cohort=(all)
  met=2  pending=7  failed=0
  first_value_milestone_reached=True
  next: First real run done
```

With `--json`: full report with `proofs` (list of metric dicts), `met_count`, `pending_count`, `failed_count`, `first_value_milestone_reached`, `suggested_next_proof_id`, `suggested_next_proof_label`.

---

## 6. Sample operator playbook

```bash
workflow-dataset operator-playbook show --id founder_operator_core
```

Example output:

```
Founder/operator vertical playbook  (founder_operator_playbook)
  setup: Complete required setup: env ready, onboard approvals, then run first-value path.
  first_value: Follow first-value path steps; use vertical-packs first-value --id founder_operator_core
  recovery: Path stalled: run the escalation command for your step, then follow the recovery path...
  when_to_narrow_scope: If user stalls repeatedly, narrow to simulate-only or fewer surfaces.
  when_to_escalate_cohort: If cohort health recommends downgrade or critical supported-surface issues.
  trust_review: workflow-dataset trust cockpit; review before_real gates.
  commands: workflow-dataset vertical-packs recovery --id founder_operator_core --step 3, workflow-dataset onboard status, ...
```

---

## 7. Exact tests run

```bash
python3 -m pytest tests/test_vertical_launch.py -v
```

Covers: list_launch_kits, build_launch_kit_for_vertical, set/get/clear active_launch, proof_state and build_success_proof_report, record_proof_met, operator_playbook in kit, supported_unsupported_boundaries. **7 passed.**

---

## 8. Remaining gaps for later refinement

- **Setup checklist gating:** Required setup items are defined but not yet evaluated against onboarding/release state (e.g. env_ready from bootstrap, approvals from onboard status); wiring to block `launch-kit start` or show blockers is optional follow-up.
- **Proof sync with milestones:** Proofs (e.g. first_simulate_done) are not yet auto-set from vertical_packs progress; `record_proof_met` is explicit; can sync from set_milestone_reached or path progress in a later pass.
- **Launch blockers derivation:** mission_control uses vertical_packs blocked_onboarding_step; could also incorporate setup checklist failures and cohort health.
- **Recovery path in CLI:** operator-playbook show does not print recovery paths step-by-step; vertical-packs recovery already exists; launch kit could link to it more explicitly.
- **Multiple verticals:** One active launch kit at a time; multi-vertical or A/B launch is out of scope for this draft.

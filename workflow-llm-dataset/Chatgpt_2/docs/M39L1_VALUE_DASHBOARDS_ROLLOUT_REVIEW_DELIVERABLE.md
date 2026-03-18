# M39L.1 — Value Dashboards + Vertical Rollout Reviews (Deliverable)

Extension of M39I–M39L: vertical value dashboards, rollout review packs, continue/narrow/pause/expand decisions, operator-facing summary. No rebuild of the vertical launch layer.

---

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/vertical_launch/models.py` | Added **RolloutDecision**, **RolloutReviewPack**; constants **ROLLOUT_CONTINUE**, **ROLLOUT_NARROW**, **ROLLOUT_PAUSE**, **ROLLOUT_EXPAND**. |
| `src/workflow_dataset/vertical_launch/store.py` | Added **save_rollout_decision**, **list_rollout_decisions**; persistence in `rollout_decisions.jsonl`. |
| `src/workflow_dataset/vertical_launch/__init__.py` | Exported dashboard, rollout_review, RolloutReviewPack, RolloutDecision, save_rollout_decision, list_rollout_decisions, get_recommended_decision. |
| `src/workflow_dataset/cli.py` | Added **value-dashboard** group: `show --id`, `list`. Added **rollout-review** group: `show --id`, `list`, `record --id --decision --rationale`. |
| `src/workflow_dataset/mission_control/state.py` | **launch_kit_state** extended with **value_dashboard_summary** (what_is_working, what_is_not_working, operator_summary), **recommended_rollout_decision**, **suggested_rollout_review**. |
| `src/workflow_dataset/mission_control/report.py` | **[Vertical launch]** section extended with recommended_rollout, suggested_rollout_review, working/not_working from value_dashboard_summary. |
| `tests/test_vertical_launch.py` | Added tests: **test_build_value_dashboard**, **test_build_rollout_review_pack**, **test_rollout_decision_record_and_list**. |

## 2. Files created

| File | Purpose |
|------|---------|
| `src/workflow_dataset/vertical_launch/dashboard.py` | **build_value_dashboard**, **list_value_dashboards** — aggregate proof, milestones, what's working/not, operator summary. |
| `src/workflow_dataset/vertical_launch/rollout_review.py` | **build_rollout_review_pack**, **list_rollout_review_packs**, **get_recommended_decision** — evidence, recommended continue/narrow/pause/expand, operator summary. |
| `docs/samples/M39L1_value_dashboard_sample.json` | Sample value dashboard output. |
| `docs/samples/M39L1_rollout_review_pack_sample.json` | Sample rollout review pack output. |
| `docs/M39L1_VALUE_DASHBOARDS_ROLLOUT_REVIEW_DELIVERABLE.md` | This deliverable. |

---

## 3. Sample value dashboard

See `docs/samples/M39L1_value_dashboard_sample.json`. Example keys:

- **launch_kit_id**, **curated_pack_id**, **label**, **launch_started_at_utc**, **is_active**
- **proof_summary**: met_count, pending_count, failed_count, first_value_milestone_reached
- **milestone_progress**: reached_milestone_ids, next_milestone_id, next_milestone_label, blocked_step_index, suggested_next_command
- **what_is_working**, **what_is_not_working**: list of short strings
- **operator_summary**: one paragraph for operators

CLI: `workflow-dataset value-dashboard show --id founder_operator_core` or `value-dashboard list`.

---

## 4. Sample rollout review pack

See `docs/samples/M39L1_rollout_review_pack_sample.json`. Example keys:

- **vertical_id**, **launch_kit_id**, **label**
- **evidence_summary**, **what_is_working**, **what_is_not_working**
- **recommended_decision**: continue | narrow | pause | expand
- **recommended_rationale**: short explanation
- **operator_summary**, **proof_met_count**, **proof_pending_count**, **first_value_reached**, **blocked_step_index**
- **previous_decisions**: list of RolloutDecision dicts
- **generated_at_utc**

CLI: `workflow-dataset rollout-review show --id founder_operator_core`, `rollout-review list`, `rollout-review record --id founder_operator_core --decision continue --rationale "On track"`.

---

## 5. Exact tests run

```bash
python3 -m pytest tests/test_vertical_launch.py -v
```

**10 passed** (including test_build_value_dashboard, test_build_rollout_review_pack, test_rollout_decision_record_and_list).

---

## 6. Next recommended step for the pane

- **Wire recommended_decision to cohort/scope:** When operator records **narrow** or **pause**, optionally drive cohort downgrade or surface narrowing (e.g. via cohort transition or vertical_selection scope lock) so the next mission_control or CLI reflects the narrower scope. Today we only record the decision; no automatic scope change.
- **Dashboard history:** Optionally persist value dashboard snapshots (e.g. daily) under `data/local/vertical_launch/dashboard_snapshots/` to show trend of what_is_working / what_is_not_working over time.
- **Rollout review from triage:** Feed triage health (open issues, supported-surface issues, recommended_downgrade) into **get_recommended_decision** so that critical or high-severity supported-surface issues push recommendation toward **pause** or **narrow**.
- **Operator checklist:** Add a short operator checklist (e.g. “before expand: N proofs met, no blocked step, no critical triage”) and expose it in mission_control or `operator-playbook show` so expand is gated by explicit criteria.

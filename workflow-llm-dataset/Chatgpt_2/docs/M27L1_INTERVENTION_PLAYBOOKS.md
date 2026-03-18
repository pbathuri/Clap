# M27L.1 — Intervention Playbooks + Stalled-Project Recovery

First-draft intervention playbooks for stalled/blocked projects: trigger pattern, operator intervention, agent next step, escalation/defer. Recovery command matches board state to a playbook and prints recommended actions.

---

## 1. Files modified

- **progress/__init__.py** — Exported InterventionPlaybook, list_playbooks, get_default_playbooks, build_stalled_recovery, format_stalled_recovery, match_playbook.
- **cli.py** — Added `progress recovery --project` and `progress playbooks`.

## 2. Files created

- **progress/playbooks.py** — InterventionPlaybook dataclass; get_default_playbooks() with four playbooks (stalled_founder_ops, blocked_analyst_case, developer_stuck_approval_capability, document_heavy_stuck_extraction_review).
- **progress/recovery.py** — match_playbook(), build_stalled_recovery(), format_stalled_recovery().
- **docs/M27L1_INTERVENTION_PLAYBOOKS.md** — This doc.

## 3. Sample intervention playbook

```python
InterventionPlaybook(
    playbook_id="stalled_founder_ops",
    title="Stalled founder ops project",
    trigger_pattern="Stalled founder-ops project: 2+ sessions with disposition fix/pause, pack founder_ops or role founder, blocked_count > 0.",
    operator_intervention="Review approval registry; unblock path/scope if safe. Run value-packs first-run for founder_ops_plus if not provisioned. Check mission-control trust cockpit. Run: workflow-dataset progress board, then replan recommend.",
    agent_next_step="Replan with current goal; suggest simulate-only next step; do not auto-execute real actions until operator confirms approvals.",
    escalation_defer_guidance="If approvals cannot be extended: defer to human; document blocker in outcomes and set disposition=fix. Use corrections add for any parameter/style fix.",
    trigger_keywords=["founder", "founder_ops", "ops"],
    trigger_cause_codes=["approval_missing", "path_scope_denied", "policy_denied"],
)
```

## 4. Sample stalled-project recovery output

Output of `workflow-dataset progress recovery --project default` when stalled and matched to founder-ops playbook:

```
=== Stalled-project recovery: default ===

[Board snapshot]
  stalled: default
  replan_needed: default
  project_health: blocked
  recurring_blockers: approval_missing(job_weekly), path_scope_denied(/tmp)

[Matched playbook] Stalled founder ops project
  Trigger: Stalled founder-ops project: 2+ sessions with disposition fix/pause, pack founder_ops or role founder, blocked_count > 0.

[Recommended operator intervention]
  Review approval registry; unblock path/scope if safe. Run value-packs first-run for founder_ops_plus if not provisioned. Check mission-control trust cockpit. Run: workflow-dataset progress board, then replan recommend.

[Recommended agent next step]
  Replan with current goal; suggest simulate-only next step; do not auto-execute real actions until operator confirms approvals.

[Escalation / defer guidance]
  If approvals cannot be extended: defer to human; document blocker in outcomes and set disposition=fix. Use corrections add for any parameter/style fix.
```

## 5. Exact tests run

```bash
python3 -m pytest tests/test_progress_replan.py -v
```

New tests: test_playbooks_default, test_playbook_has_all_fields, test_match_playbook_by_cause, test_match_playbook_stalled_default, test_build_stalled_recovery, test_format_stalled_recovery.

## 6. Next recommended step for the pane

- **Wire recovery into mission control** — Add `next_recovery_playbook` or `recovery_recommended_for` to the progress_replan section when a project is stalled, so the dashboard suggests `progress recovery --project <id>`.
- **Configurable playbooks** — Allow loading playbooks from data/local/progress/playbooks.json so operators can add or override playbooks without code changes.
- **Pack/session context in match** — Pass pack_id and session disposition from outcomes into match_playbook so analyst/founder/document playbooks match on actual pack_id from session outcome history.

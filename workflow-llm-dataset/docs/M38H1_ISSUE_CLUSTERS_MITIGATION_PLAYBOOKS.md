# M38H.1 — Issue Clusters + Mitigation Playbooks (Deliverable)

Extends M38E–M38H cohort evidence/triage layer (no rebuild). First-draft support for issue clusters by subsystem/workflow/cohort, mitigation playbooks, operator “do now” guidance, and links from cohort health to support/recovery/readiness.

---

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/cli.py` | Added **triage clusters** (list clusters by subsystem/workflow/cohort), **triage playbook** (show one or list all), **triage do-now** (operator guidance and links by issue or cluster). Cohort health human output now prints next_action_links line (support / recovery / readiness) when there are open issues. |
| `src/workflow_dataset/triage/health.py` | Added **next_action_links** to cohort health summary: list of `{ "label": "support"|"recovery"|"readiness", "command": "..." }` so JSON consumers get explicit links into support/recovery/readiness surfaces. |

## 2. Files created

| File | Purpose |
|------|---------|
| `docs/samples/M38H1_sample_issue_cluster.json` | Sample issue cluster (by subsystem). |
| `docs/samples/M38H1_sample_mitigation_playbook.json` | Sample mitigation playbook with operator_do_now and links. |
| `docs/M38H1_ISSUE_CLUSTERS_MITIGATION_PLAYBOOKS.md` | This deliverable. |

**Existing (unchanged):** `triage/models.py` (IssueCluster, MitigationPlaybook, OperatorDoNow), `triage/clusters.py`, `triage/playbooks.py` — already implement clusters by subsystem/workflow/cohort and default playbooks with do-now and links.

## 3. Sample issue cluster

See `docs/samples/M38H1_sample_issue_cluster.json`:

```json
{
  "cluster_id": "cluster_executor_a1b2c3",
  "cohort_id": "broader_ops_q1",
  "subsystem": "executor",
  "workflow_or_context": "ops_reporting",
  "issue_ids": ["issue_abc123", "issue_def456"],
  "severity": "high",
  "summary": "executor: 2 issue(s)",
  "playbook_id": "executor_blocked",
  "created_at_utc": "2025-03-16T16:00:00.000000+00:00"
}
```

CLI: `triage clusters --by subsystem` or `triage clusters --by workflow --cohort X --json`.

## 4. Sample mitigation playbook

See `docs/samples/M38H1_sample_mitigation_playbook.json`:

```json
{
  "playbook_id": "executor_blocked",
  "label": "Executor / run blocked",
  "description": "Issues involving executor, run blocked, or step failure.",
  "steps": ["Run: workflow-dataset recovery suggest --subsystem executor", ...],
  "operator_do_now": {
    "guidance": "Check recovery guide for executor; run reliability to reproduce.",
    "link_support": "workflow-dataset release triage",
    "link_recovery": "workflow-dataset recovery suggest --subsystem executor",
    "link_readiness": "workflow-dataset release report",
    "commands": ["recovery suggest --subsystem executor", "reliability run"]
  },
  "related_subsystems": ["executor", "supervised_loop", "background_run"],
  "when_to_use": "Executor step failed, run blocked, or automation handoff."
}
```

CLI: `triage playbook` (list all), `triage playbook --id executor_blocked`, `triage do-now --issue-id X` or `triage do-now` (uses highest-severity cluster).

## 5. Exact tests run

```bash
cd /Users/prady/Desktop/Clap/workflow-llm-dataset
.venv/bin/python -m pytest tests/test_triage.py -v
```

Relevant tests (included in full run): `test_build_clusters_by_subsystem`, `test_build_clusters_by_cohort`, `test_get_playbook_for_subsystem`, `test_get_playbook_for_issue`, `test_health_includes_clusters_and_links`. Full suite: 17 passed.

## 6. Next recommended step for the pane

- **Wire clusters into mission control:** Add to the triage block in `mission_control/state.py`: `top_cluster_id`, `top_cluster_playbook_id`, and optionally `next_action_links` (from cohort health) so the report can show “Do now: …” and “Run: …” for the highest-severity cluster.
- **Custom playbooks:** Allow loading playbooks from `data/local/triage/playbooks.yaml` (or similar) so operators can add cohort- or org-specific playbooks and override defaults.
- **Cluster → issue detail:** Add `triage cluster show --id CLUSTER_ID` to list issue_ids and show playbook + do-now for that cluster.
- **Cohort health JSON:** When calling `cohort health --json`, ensure `next_action_links` is present and that UIs can render “Support / Recovery / Readiness” as clickable or copy-paste commands.
- **Recovery/supportability CLI names:** If the actual CLI is not `workflow-dataset` but e.g. `workflow-dataset`, ensure playbook strings match the installed entry point so operators can copy-paste.

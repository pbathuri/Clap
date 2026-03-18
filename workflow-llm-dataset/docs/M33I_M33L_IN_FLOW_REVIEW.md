# M33I–M33L In-Flow Review Studio + Draft / Handoff Composer

First-draft in-flow review and composition layer: create drafts at workflow moments, stage summaries/checklists/decisions, review and revise in context, promote to artifact, hand off to approval/planner/executor/workspace.

## Features

- **Draft artifacts**: Created at key workflow moments; tied to project, session, step, episode. Types: status_summary, review_checklist, next_step_handoff_brief, blocked_item_escalation_note, meeting_follow_up, approval_request_summary, draft_update, other.
- **Handoff packages**: From workflow/session (e.g. `--from-workflow latest`); summary, next_steps, optional draft refs; target: artifact, approval_studio, planner, executor, workspace.
- **Review checkpoints**: Linked to plan step; optional draft_id; status pending/reviewed/skipped.
- **Staged items**: stage_summary, stage_checklist, stage_decision_request (in-memory/staging; can be turned into drafts).
- **Contextual review**: get_draft_in_context, revise_draft, attach_note, promote_to_artifact, handoff_to_target.

## CLI

| Command | Description |
|--------|-------------|
| `workflow-dataset drafts list` | List drafts (optional --project, --status, --limit) |
| `workflow-dataset drafts create --type status_summary --project founder_case_alpha` | Create in-flow draft |
| `workflow-dataset drafts review --id draft_xxx` | Inspect draft in context |
| `workflow-dataset handoffs create --from-workflow latest` | Create handoff from current workflow |
| `workflow-dataset handoffs show --id handoff_xxx` | Show handoff contents |

Use `--repo /path` when not in repo root.

## Sample draft artifact (JSON-like)

```json
{
  "draft_id": "draft_abc123",
  "draft_type": "status_summary",
  "title": "Status summary",
  "content": "# Status summary\n\n**Goal:** ...\n**Steps:**\n- 1. ...",
  "project_id": "founder_case_alpha",
  "session_id": "sess_1",
  "affected_step": {
    "step_index": 0,
    "plan_id": "plan_1",
    "step_label": "Review deliverables",
    "run_id": "",
    "episode_id": ""
  },
  "review_status": "waiting_review",
  "created_utc": "2025-03-16T12:00:00Z",
  "updated_utc": "2025-03-16T12:00:00Z",
  "revision_history": [],
  "operator_notes": "",
  "promoted_artifact_path": "",
  "handed_off_to": ""
}
```

## Sample handoff package

```json
{
  "handoff_id": "handoff_def456",
  "from_workflow": "latest",
  "from_session_id": "sess_1",
  "from_project_id": "default",
  "title": "Handoff from latest",
  "summary": "Goal: Complete Q1 review. Next: run report job.",
  "next_steps": ["Run report job", "Update dashboard"],
  "draft_ids": ["draft_abc123"],
  "target": "artifact",
  "target_ref": "",
  "created_utc": "2025-03-16T12:00:00Z",
  "delivered_utc": ""
}
```

## Sample contextual review flow

1. Create draft: `workflow-dataset drafts create --type status_summary --project founder_case_alpha`
2. List: `workflow-dataset drafts list --status waiting_review`
3. Review in context: `workflow-dataset drafts review --id draft_xxx` (shows content, affected step, notes)
4. Revise (API): `revise_draft("draft_xxx", new_content, summary="Updated")`
5. Attach note (API): `attach_note("draft_xxx", "LGTM after edit")`
6. Promote (API): `promote_to_artifact("draft_xxx", "artifacts/summary.md")`
7. Create handoff: `workflow-dataset handoffs create --from-workflow latest --target artifact`
8. Deliver handoff (API): `handoff_to_target("handoff_xxx")` → writes handoff summary to `data/local/in_flow/handoffs/handoff_xxx.md`

## Mission control

- **in_flow** block: latest_draft_waiting_review_id, active_review_checkpoint_id, latest_handoff_id, latest_handoff_target, recent_promoted_draft_ids, drafts_waiting_count, checkpoints_pending_count.
- Report section **[In-flow]**: draft_waiting, checkpoint, latest_handoff, target, counts.

## Storage

- `data/local/in_flow/drafts.json` — draft artifacts
- `data/local/in_flow/handoffs.json` — handoff packages
- `data/local/in_flow/checkpoints.json` — review checkpoints
- `data/local/in_flow/handoffs/<handoff_id>.md` — delivered handoff artifact (when target=artifact)

## Tests

```bash
pytest tests/test_in_flow.py -v
```

Covers: draft/handoff/checkpoint models, save/load/list, create_draft, create_handoff, get_draft_in_context, revise_draft, attach_note, promote_to_artifact, handoff_to_target, link_checkpoint_to_step.

## Constraints

- No hidden content generation: drafts are template + context (plan, session).
- Trust/approval: handoff to approval_studio/executor does not bypass existing gates.
- Not a full document editor: content is markdown/outline; revise replaces content and appends revision.

## Remaining gaps (for later refinement)

- **Workflow episode integration**: Resolve `episode_ref` and `from_workflow` from workflow-episode tracking (Pane 1) when available.
- **Step awaiting composed output**: Mission control could surface “current step has no draft yet” from plan + checkpoints.
- **Regenerate draft**: Optional “regenerate” from same template + fresh context (e.g. after plan change).
- **CLI for revise/promote/handoff deliver**: Expose `drafts revise --id --content`, `drafts promote --id --path`, `handoffs deliver --id` in CLI.
- **Staged summary/checklist persistence**: Persist staged items to store if needed for multi-step flows.

---

## Final deliverable summary (M33I–M33L)

### Files created

| Path | Purpose |
|------|--------|
| `src/workflow_dataset/in_flow/__init__.py` | Package exports |
| `src/workflow_dataset/in_flow/models.py` | DraftArtifact, HandoffPackage, ReviewCheckpoint, StagedSummary/Checklist/DecisionRequest, AffectedWorkflowStep, RevisionEntry |
| `src/workflow_dataset/in_flow/store.py` | save/load/list drafts, handoffs, checkpoints; append_revision |
| `src/workflow_dataset/in_flow/composition.py` | create_draft, create_handoff, stage_summary/checklist/decision_request, link_checkpoint_to_step |
| `src/workflow_dataset/in_flow/review.py` | get_draft_in_context, revise_draft, attach_note, promote_to_artifact, handoff_to_target |
| `docs/M33I_M33L_IN_FLOW_REVIEW_ANALYSIS.md` | Pre-coding analysis (what exists, gaps, file plan, safety, what we do not do) |
| `docs/M33I_M33L_IN_FLOW_REVIEW.md` | User doc, CLI, samples, tests, gaps |
| `tests/test_in_flow.py` | Model, store, composition, review, promote, handoff, checkpoint tests |

### Files modified

| Path | Change |
|------|--------|
| `src/workflow_dataset/cli.py` | Added `drafts_group` (list, create, review) and `handoffs_group` (create, show) |
| `src/workflow_dataset/mission_control/state.py` | Added `in_flow` block (latest_draft_waiting_review, active_checkpoint, latest_handoff, recent_promoted, counts) |
| `src/workflow_dataset/mission_control/report.py` | Added [In-flow] section |

### Exact CLI usage

```bash
workflow-dataset drafts list [--project PROJECT] [--status STATUS] [--limit N]
workflow-dataset drafts create --type status_summary [--project founder_case_alpha] [--session SESSION] [--title TITLE]
workflow-dataset drafts review --id draft_xxx
workflow-dataset handoffs create [--from-workflow latest] [--session SESSION] [--project PROJECT] [--title TITLE] [--target artifact]
workflow-dataset handoffs show --id handoff_xxx
```

### Exact tests run

```bash
pytest tests/test_in_flow.py -v
```

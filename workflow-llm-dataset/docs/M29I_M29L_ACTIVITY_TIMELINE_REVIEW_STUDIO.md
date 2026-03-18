# M29I–M29L Activity Timeline + Review Studio + Intervention Inbox

First-draft unified activity timeline, intervention inbox, and review studio for local operator review and intervention. Does not replace existing approval queue, daily inbox, or mission control; aggregates and adds a single place to see what happened, what needs review, and where to intervene.

---

## 1. CLI / surface usage

### Timeline
- `workflow-dataset timeline latest [--limit 40] [--since <ISO>] [--repo-root <path>]` — latest activity across queue, executor, policy, projects, skills, replan.
- `workflow-dataset timeline project --id <project_id> [--limit 30] [--repo-root <path>]` — timeline filtered by project.

### Intervention inbox (under existing `inbox` group)
- `workflow-dataset inbox list [--status pending] [--limit 50] [--repo-root <path>]` — list intervention items (approval queue, blocked runs, replan, skills, policy, stalled).
- `workflow-dataset inbox review --id <item_id> [--repo-root <path>]` — inspect item: why it matters, link commands.
- `workflow-dataset inbox accept --id <item_id> [--note "..."] [--repo-root <path>]` — accept (delegates to agent-loop approve or teaching accept).
- `workflow-dataset inbox reject --id <item_id> [--note "..."] [--repo-root <path>]` — reject (delegates to agent-loop reject or teaching reject).
- `workflow-dataset inbox defer --id <item_id> [--note "..."] [--revisit-after <ISO>] [--repo-root <path>]` — defer (delegates to agent-loop defer when applicable).

### Mission control
- Report includes **[Review studio]** section: `timeline=N inbox=M urgent=K`, oldest unresolved id hint, and `timeline latest | inbox list | inbox review --id <item_id>`.

---

## 2. Sample timeline output

```
Activity timeline (newest first)
┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ time              ┃ kind                     ┃ summary                                                  ┃
┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 2025-03-16T14:32  │ policy_override_applied  │ Policy override: manual_only=False                        │
│ 2025-03-16T14:30  │ action_approved          │ Action approved: q_abc123                                │
│ 2025-03-16T14:28  │ executor_started         │ Run started: exec_xyz                                    │
│ 2025-03-16T14:25  │ action_queued            │ Action queued: Run founder_ops_plus (simulate)            │
└───────────────────┴──────────────────────────┴──────────────────────────────────────────────────────────┘
Filter: workflow-dataset timeline project --id <project_id>
```

---

## 3. Sample inbox item

From `workflow-dataset inbox list`:

| item_id | kind | priority | summary |
|---------|------|----------|---------|
| inbox_a1b2c3d4e5... | approval_queue | high | Run founder_ops_plus (simulate) |
| inbox_f6g7h8... | blocked_run | high | Run blocked: exec_xyz |
| inbox_r9s0... | replan_recommendation | medium | Replan recommended: founder_case_alpha |

Item structure (from code): `item_id`, `kind`, `status`, `summary`, `created_at`, `priority`, `entity_refs`, `source_ref`, `operator_notes`, `decided_at`, `decision_note`, `revisit_after`.

---

## 4. Sample review flow output

**`workflow-dataset inbox review --id inbox_a1b2c3d4e5...`**

```
Inbox item
  item_id: inbox_a1b2c3d4e5...
  kind: approval_queue  status: pending  priority: high
  summary: Run founder_ops_plus (simulate)
  why_matters: Proposed agent action awaiting approval; approve/reject/defer to advance or block.
Link commands
  workflow-dataset agent-loop queue
  workflow-dataset agent-loop approve --id q_abc123
inbox accept --id inbox_a1b2c3d4e5...  |  inbox reject --id ...  |  inbox defer --id ...
```

**`workflow-dataset inbox accept --id inbox_a1b2c3d4e5...`**

```
Accepted inbox_a1b2c3d4e5...
```

---

## 5. Tests run

```bash
python3 -m pytest tests/test_review_studio.py -v
```

Covers: timeline empty and project filter, inbox pending/all, get_item/inspect_item unknown, TimelineEvent and InterventionItem roundtrip, operator notes save/load, inbox snapshot after build.

---

## 6. Remaining gaps for later refinement

- **Lane results**: Lane “results awaiting acceptance” are not yet collected into the inbox (worker_lanes result review); add when lane review API is stable.
- **Artifact review**: Artifact-produced/reviewed events and artifact_review inbox kind are in the model but not yet populated from release/workspace artifact state.
- **Stable item_id**: Inbox item_id is derived from kind+source_ref (and for replan, date); same logical item keeps the same id across runs. No persistent inbox store yet—items are rebuilt each time.
- **Defer for non-queue items**: Replan/stalled/policy items support “defer” only by recording a note; no revisit_after enforcement.
- **Timeline event persistence**: Timeline is built on demand from domain stores; no dedicated event log. Adding a write path (e.g. on approve/reject/run) would allow a single ordered event store.
- **Empty-state copy**: When timeline or inbox is empty, CLI shows a short dim message; could add “what to do next” or link to onboarding.
- **Lane created/returned/failed events**: Timeline event kinds exist; population from worker_lanes is not yet wired.

---

*Ref: M29I_M29L_ACTIVITY_TIMELINE_REVIEW_STUDIO_ANALYSIS.md (pre-coding analysis).*

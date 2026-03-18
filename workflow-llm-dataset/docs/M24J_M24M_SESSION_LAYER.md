# M24J–M24M — Live Workspace Session Layer

First-draft session system: launch a live workspace from a provisioned pack, track active work context, task board, artifact hub, and mission control visibility. Local, pack-aware, no cloud.

---

## 1. Files modified

| File | Change |
|------|--------|
| `cli.py` | Added `session_group`: commands `start`, `status`, `board`, `artifacts`, `close`, `list`. |
| `mission_control/state.py` | Added block `active_session`: session_id, pack_id, queued_count, blocked_count, ready_count, artifacts_count, recommended_next_session_action. |
| `mission_control/report.py` | Added `[Session]` section: session_id, pack, queued/blocked/ready/artifacts, next action. |

## 2. Files created

| File | Purpose |
|------|--------|
| `session/models.py` | Session dataclass: session_id, value_pack_id, starter_kit_id, profile_ref, active_tasks/job_ids/routine_ids/macro_ids, current_artifacts, notes, state, timestamps, trust/capability context, recommended_next_actions. |
| `session/storage.py` | get_sessions_dir, save_session, load_session, load_current_session_id, set_current_session_id, list_sessions, archive_session. Persist under `data/local/session/`. |
| `session/artifacts.py` | add_artifact, list_artifacts, add_note, get_notes, add_output, get_handoff, set_handoff. Persist under `data/local/session/<session_id>/`. |
| `session/launch.py` | start_session(pack_id), resume_session(session_id), close_session(session_id), get_current_session. Validates pack provisioned for start. |
| `session/board.py` | build_session_board(session): active tasks, queued (paused/awaiting_approval), blocked (macro steps + job blocking_issues), ready, completed (plan runs + macro runs), artifacts_produced. |
| `session/report.py` | format_session_status, format_session_board, format_session_artifact_hub. |
| `session/__init__.py` | Re-exports public API. |
| `tests/test_session.py` | 13 tests: model roundtrip, storage save/load, current id, start (provisioned/unknown pack), resume/close, board build, artifact hub, format status/board, list_sessions, archive. |
| `docs/M24J_M24M_SESSION_LAYER_ANALYSIS.md` | Before-coding: existing surfaces, gaps, file plan, safety, out-of-scope. |
| `docs/M24J_M24M_SESSION_LAYER.md` | This doc. |

---

## 3. Exact CLI usage

```bash
workflow-dataset session start --pack founder_ops_plus [--repo-root PATH]
workflow-dataset session status [--repo-root PATH]
workflow-dataset session board [--repo-root PATH]
workflow-dataset session artifacts [--repo-root PATH]
workflow-dataset session close [--id SESSION_ID] [--repo-root PATH]
workflow-dataset session list [--repo-root PATH] [--limit N] [--state open|closed|archived]
```

- **start:** Pack must be provisioned (`workflow-dataset packs provision --id founder_ops_plus`). Creates session, sets as current.
- **status:** Shows current session id, pack, state, created/updated.
- **board:** Active tasks, queued (paused/awaiting-approval macro runs), blocked, ready, recently completed, artifacts this session.
- **artifacts:** Artifacts, notes, handoff summary/next_steps for current session.
- **close:** Closes and archives session; if `--id` omitted, closes current. Clears current pointer if it was current.
- **list:** Lists sessions (most recent first); optional filter by state.

---

## 4. Sample session record

```json
{
  "session_id": "session_a1b2c3d4e5f6",
  "value_pack_id": "founder_ops_plus",
  "starter_kit_id": "founder_ops_starter",
  "profile_ref": "",
  "active_tasks": [],
  "active_job_ids": ["weekly_status_from_notes", "weekly_status"],
  "active_routine_ids": ["morning_reporting", "morning_ops", "weekly_review"],
  "active_macro_ids": ["morning_ops"],
  "current_artifacts": [],
  "notes": [],
  "state": "open",
  "created_at": "2024-03-16T12:00:00.000000Z",
  "updated_at": "2024-03-16T12:05:00.000000Z",
  "closed_at": "",
  "trust_context": {},
  "capability_context": {},
  "recommended_next_actions": []
}
```

Stored at `data/local/session/<session_id>.json`. Current session id at `data/local/session/current_session_id.json`.

---

## 5. Sample session board

```
=== Session task board ===

[Active tasks]
  job  weekly_status_from_notes
  job  weekly_status
  routine  morning_reporting
  routine  morning_ops
  macro  morning_ops

[Queued (paused / awaiting approval)]
  morning_ops  run_id=run_xyz  status=paused
  (none)

[Blocked]
  job  weekly_status_from_notes  approval_required
  (none)

[Ready]
  job  weekly_status
  routine  morning_ops

[Recently completed]
  plan_run  run_abc  weekly_status  success
  macro_run  run_def  morning_ops

[Artifacts this session]
  data/local/copilot/runs/run_abc  (file)
  (none)
```

---

## 6. Sample session artifact hub summary

```
=== Session artifacts (session_a1b2c3d4e5f6) ===

[Artifacts]
  data/local/copilot/runs/run_abc  kind=file
  staging/weekly_brief.md  kind=output

[Notes]
  Ran first simulate; ready for real after approvals.

[Handoff]
  Summary: Session focused on founder_ops_plus; morning_ops simulated.
  Next: workflow-dataset jobs run --id weekly_status_from_notes --mode real
  Next: workflow-dataset session close when done
```

---

## 7. Exact tests run

```bash
pytest tests/test_session.py -v --tb=short
```

**Result: 13 passed.** Covers: session model roundtrip, storage save/load, current session id, start (provisioned or unknown pack), resume and close, board build, artifact hub (add_artifact, add_note, set_handoff, list_artifacts, get_notes, get_handoff), format_session_status (empty and with session), format_session_board (empty), list_sessions, archive_session.

---

## 8. Remaining gaps for later refinement

- **Profile ref:** `start_session(..., profile_ref="")` is not yet wired to onboarding user_work_profile; could pass field/job_family into session for display.
- **Trust/capability snapshot:** Session model has `trust_context` and `capability_context` but they are not populated on start; can be filled from trust cockpit and capability health for display.
- **Recommended next actions:** Session.recommended_next_actions is not auto-populated from board or daily digest; mission control recommends "session board" or "session artifacts" generically.
- **Add artifact from CLI:** No `session add-artifact` or `session add-note` CLI yet; artifacts/notes are addible only via API (e.g. from jobs/copilot when they record outputs).
- **Completed items:** Board "completed" is last N plan runs and macro runs globally, not filtered by session start time; could restrict to "since session created" for a tighter view.
- **Resume by pack:** No `session resume --pack founder_ops_plus` to resume latest open session for that pack; only resume by session_id.
- **Session-scoped reminders/copilot:** Daily digest and copilot recommend are global; could later filter by session pack job/routine ids for a session-scoped inbox.

# M24J–M24M Live Workspace Session Layer — Before Coding

## 1. What active user/work surfaces already exist

| Surface | Location | What it does |
|--------|----------|--------------|
| **Provisioning** | provisioning/* | run_provisioning(value_pack_id), check_prerequisites, domain_environment_summary(pack_id) — what's provisioned, jobs/routines/macros ready, recommended first-value run. |
| **Value packs** | value_packs/* | list_value_packs, get_value_pack, recommend_value_pack, build_first_run_flow, domain-env; pack_id, starter_kit_id, recommended_job_ids, recommended_routine_ids, recommended_macro_ids. |
| **Starter kits** | starter_kits/* | list_kits, get_kit, recommend_kit_from_profile; FirstValueFlow. |
| **Job packs** | job_packs | list_job_packs, get_job_pack, job_packs_report, run_job, preview_job; trusted_for_real, approval_blocked, simulate_only. |
| **Copilot** | copilot/* | recommend_jobs, list_routines, get_routine, build_plan_for_job/routine, run_plan, list_plan_runs; reminders, seed_morning_routine. |
| **Daily inbox** | daily/* | build_daily_digest → DailyDigest: relevant_job_ids, relevant_routine_ids, inbox_items, blocked_items, recommended_next_action, top_next_recommended. |
| **Macros** | macros/* | list_macros, macro_run, macro_preview, get_blocked_steps; list_paused_runs, list_awaiting_approval_runs, list_all_macro_runs, resume_macro_run. |
| **Context** | context/* | build_work_state → WorkState; save_snapshot, load_snapshot, compare_snapshots; work_state_to_dict. |
| **Mission control** | mission_control/* | get_mission_control_state aggregates product, eval, job_packs, work_context, copilot, value_packs, provisioning, acceptance, rollout, activation_executor, etc.; format_mission_control_report. |
| **Local deployment** | local_deployment/* | get_deployment_dir, run_first_run, run_install_check, build_local_deployment_profile. |
| **Rollout** | rollout/* | load_rollout_state, demos, launcher, support_bundle, readiness, issues, runbooks. |

None of these expose a **single active workspace session** tied to a pack, with a task board and session-scoped artifacts.

---

## 2. What is missing for a real live-session layer

- **Session entity:** No session id, no "current session" tied to a value pack / starter kit, no created_at/updated_at/closed_at.
- **Launch / resume / close:** No "start session from provisioned pack", "resume prior session", "close/archive session", or "show current session".
- **Session task board:** No single view of active tasks, queued routines/macros, blocked items, ready items, recently completed, and artifacts produced this session.
- **Session artifact hub:** No session-scoped persistence for artifacts, notes, generated outputs, task summaries, or next-step handoff.
- **Mission control:** No "active session", "pack in use", "session queued/blocked/ready", "latest session artifacts", or "recommended next session action".
- **Pack-aware daily use:** WorkState and DailyDigest are global; they are not scoped to "this session's pack" for a focused workspace feel.

---

## 3. Exact file plan

| File | Purpose |
|------|--------|
| **session/models.py** (new) | Session dataclass: session_id, value_pack_id, starter_kit_id, profile_ref, active_tasks, active_job_ids, active_routine_ids, active_macro_ids, current_artifacts, notes, state (open/closed/archived), timestamps, optional trust/capability snapshot, recommended_next_actions. |
| **session/storage.py** (new) | get_sessions_dir, save_session, load_session, load_current_session_id, set_current_session_id, list_sessions, archive_session. Persist under data/local/session/. |
| **session/board.py** (new) | build_session_board(session, repo_root): active, queued (paused/awaiting_approval), blocked (macro blocked + digest blocked), ready (pack jobs/routines not blocked), completed (from run history / session), artifacts_produced. |
| **session/artifacts.py** (new) | add_artifact, list_artifacts, add_note, get_notes, add_output, get_handoff; persist under data/local/session/<session_id>/. |
| **session/launch.py** (new) | start_session(pack_id, repo_root, profile_ref=None), resume_session(session_id, repo_root), close_session(session_id, repo_root). Validate pack provisioned for start. |
| **session/report.py** (new) | format_session_board, format_session_artifact_hub, format_session_status. |
| **session/__init__.py** (new) | Re-export public API. |
| **cli.py** (modify) | Add session_group: start --pack, status, board, artifacts, close, list. |
| **mission_control/state.py** (modify) | Add active_session block: session_id, pack_id, board summary (queued_count, blocked_count, ready_count), latest_artifacts_count, recommended_next_session_action. |
| **mission_control/report.py** (modify) | Add [Session] section. |
| **tests/test_session.py** (new) | start/resume/close, board generation, artifact hub, pack-linked state, empty/blocked handling. |
| **docs/M24J_M24M_SESSION_LAYER.md** (new) | Summary, CLI, sample record/board/artifact hub, tests, gaps. |

---

## 4. Safety / risk note

- **Local only:** All session state under `data/local/session/`. No cloud sync, no network.
- **Read-only use of existing systems:** Session layer reads job_packs, copilot, macros, provisioning, value_packs; it does not change their behavior or persistence. Board aggregates existing lists (paused runs, blocked steps, recommend_jobs) without executing anything.
- **No auto-execution:** Starting or resuming a session does not run jobs/macros; it only sets current session and persists metadata.
- **Trust:** We can store a minimal trust/capability context snapshot (e.g. approval_registry_exists, safe_to_expand) for display only; we do not bypass approval gates.
- **Risk:** If multiple processes write current_session_id simultaneously, last write wins; acceptable for first draft. No file locking.

---

## 5. What this block will NOT do

- Rebuild copilot, jobs, macros, or provisioning.
- Add cloud sync or multi-user collaboration.
- Auto-run hidden work when session starts.
- Broaden into a full collaboration or cloud workspace product.
- Replace WorkState/DailyDigest; it adds a session-scoped layer on top.

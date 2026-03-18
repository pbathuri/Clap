# M37I–M37L Durable State Persistence + Startup/Resume Performance — Before Coding

## 1. What persistence/startup/resume/recovery behavior already exists

- **Workday (day/*):** `data/local/workday/state.json`, `summaries/<day_id>.json`, `active_preset.txt`. `load_workday_state()` returns default `WorkdayStateRecord()` if file missing or on JSON/read exception. No version field, no health check, no stale marker.
- **Continuity (continuity_engine/*):** `data/local/continuity_engine/` — last_session.json, last_shutdown.json, carry_forward.json, next_session.json, rhythm_templates.json, active_rhythm_template_id.txt. Loaders return None or [] on missing/exception. Resume flow uses workday + last shutdown + next_session_recommendation + workspace context.
- **Unified queue:** No persisted queue state; builds at runtime from review_studio + automation_inbox. Queue “state” is derived.
- **Project case (projects/*):** `data/local/project_case/` — current_project_id.json, projects/<id>/project.json, goals.json, links. Load/save with JSON; no explicit recovery.
- **Session:** storage under data/local (session board, artifacts); load on demand.
- **Background run:** `data/local/background_run/` — queue.json, history.json, runs/, retry_policies.json. list_runs/load_run; degraded_fallback for blocked runs.
- **Reliability:** `data/local/reliability/runs/`; recovery_playbooks (in code) for broken_pack_state, failed_upgrade, missing_runtime, blocked_approval, stuck_project, invalid_workspace. Degraded profiles and fallback matrix for subsystem unavailability.
- **Mission control:** Aggregates many subsystems read-only; records `local_sources` paths. No dedicated “state health” or “startup readiness” or “resume quality” block.
- **Install/upgrade, degraded modes:** Docs (M30H1, M34H1) describe degraded fallbacks and retry policies; no single startup “readiness” gate.

## 2. What is missing for true long-run durability

- **Cross-cutting state health:** No single place that checks workday, continuity, project, background_run, review_studio, automation_inbox for readable/coherent state and reports health.
- **Explicit recoverable partial state:** No model for “some subsystems ok, some missing/corrupt” with a safe path to resume.
- **Startup readiness:** No ordered “startup health checks” or “hydration order” or “fast path for most recent coherent state.”
- **Resume target:** Continuity has resume flow and strongest_resume_target; no unified “resume target” that combines workday + continuity + project + optional queue hint for one recommended first action.
- **Stale/corrupt/incomplete markers:** No explicit stale-state marker or corrupted-state note persisted or reported; loaders silently return defaults.
- **Persistence boundaries:** No registry of “which subsystem owns which path” and “last write time” for staleness or reconciliation.
- **Long-run maintenance:** No stale-state cleanup, partial-state reconciliation, background/result compaction, or old queue/timeline summarization; no startup-time readiness summary.
- **CLI and mission control:** No `state health`, `state snapshot`, `state reconcile`, `state startup-readiness`, `state resume-target`; no mission_control visibility for state health, resume quality, warnings, or recommended recovery action.

## 3. Exact file plan

| Path | Purpose |
|------|---------|
| `src/workflow_dataset/state_durability/__init__.py` | Package exports |
| `src/workflow_dataset/state_durability/models.py` | DurableStateSnapshot, RecoverablePartialState, StartupReadiness, ResumeTarget, StaleStateMarker, CorruptedStateNote, PersistenceBoundary |
| `src/workflow_dataset/state_durability/boundaries.py` | Persistence boundaries by subsystem (workday, continuity, project_case, background_run, review_studio, automation_inbox, etc.), path and optional last_write / health |
| `src/workflow_dataset/state_durability/startup_health.py` | Health checks per boundary, startup_readiness aggregation, hydration order, degraded resume when parts missing |
| `src/workflow_dataset/state_durability/resume_target.py` | Build best resume target from workday + continuity + project; fast path for “most recent coherent” |
| `src/workflow_dataset/state_durability/maintenance.py` | Stale-state cleanup (configurable), partial-state reconciliation (inspectable), readiness summary at startup |
| `src/workflow_dataset/state_durability/store.py` | Optional: save/load DurableStateSnapshot or StartupReadiness for fast path (e.g. last_known_good) |
| `src/workflow_dataset/cli.py` | Add `state_group`: health, snapshot, reconcile, startup-readiness, resume-target |
| `src/workflow_dataset/mission_control/state.py` | Add `state_durability_state` block: state_health, resume_quality, stale/corrupt/incomplete warnings, recommended_recovery_action |
| `src/workflow_dataset/mission_control/report.py` | Add [State durability] section from state_durability_state |
| `tests/test_state_durability.py` | Tests: startup health, resume target, partial-state recovery, stale handling, degraded startup, snapshot/reconcile |
| `docs/M37I_M37L_DURABLE_STATE.md` | Spec, CLI, sample outputs, tests, remaining gaps |

## 4. Safety/risk note

- **Read-heavy:** Health and startup-readiness will read many paths; avoid writing unless explicitly requested (e.g. reconcile with a flag). Reconcile must not overwrite user state blindly; prefer “report and suggest” or explicit compaction steps.
- **No cloud:** All state remains local; no cloud sync or external state dependency.
- **Visibility:** Do not hide degraded or corrupt state; expose warnings and recommended recovery so the operator can act.
- **Backward compatible:** Existing loaders keep current behavior; durability layer is additive (health checks, new CLI, mission_control block).

## 5. Hardening principles

- **Inspectable:** All state and health outcomes visible via CLI and mission control; no silent fixes.
- **Local-first:** No new network or cloud dependency.
- **Graceful degradation:** When a subsystem fails to load, report it and allow “degraded but usable” startup with a clear recommended recovery action.
- **Fast path:** Prefer “most recent coherent working state” for resume (e.g. continuity last shutdown + workday + project) so daily reuse is stable and quick.
- **Boundaries:** Explicit persistence boundaries per subsystem so we know what to check and in what order.

## 6. What this block will NOT do

- Will not rebuild the whole storage model or replace existing stores.
- Will not add cloud state sync or external state dependencies.
- Will not hide degraded or corrupt state.
- Will not over-engineer beyond product needs (no generic infra unrelated to workday/queue/continuity/automation).
- Will not change existing loader contracts; only add a layer on top for health, readiness, resume target, and optional maintenance.

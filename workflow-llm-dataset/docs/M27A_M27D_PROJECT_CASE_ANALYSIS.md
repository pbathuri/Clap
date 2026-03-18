# M27A–M27D — Project/Case Graph + Persistent Goal Stack — Before Coding

## 1. What persistent or project-adjacent state already exists

| Area | What exists | Scope / limit |
|------|-------------|----------------|
| **Session** | `Session` model (session_id, value_pack_id, active_tasks, active_job_ids, artifacts, state open/closed/archived). Stored under `data/local/session/<session_id>.json`. `current_session_id.json` points to active session. `list_sessions`, `archive_session`. | Per-session; no project/case parent. Sessions are not grouped by a long-lived project. |
| **Outcomes** | `SessionOutcome`, `TaskOutcome`, `ArtifactOutcome`; stored under `data/local/outcomes/sessions/`. Outcome history by session_id. | Tied to session_id; no project_id. |
| **Planner** | Single `current_goal.txt` and `latest_plan.json` under `data/local/planner/`. Plan has steps, edges, checkpoints, blocked_conditions. | One global “current goal” and one “latest plan”; not scoped to a project or case. No goal stack or history per project. |
| **Executor** | `ExecutionRun` (run_id, plan_id, status, artifacts) under `data/local/executor/runs/<run_id>/`. `list_runs`, `load_run`, `save_run`. | Runs are not linked to a project or case. |
| **Coordination graph** | Task-level graph (nodes/edges per task_id). Advisory only. | No project-level graph. |
| **Context / work state** | `WorkState` snapshot: jobs, intake, approvals, reminders, recent plan runs. | Snapshot of “current” work; not a persistent project entity. |
| **Mission control** | Aggregates product_state, evaluation_state, development_state, incubator, pack_registry, pack_behavior, pack_authoring, goal_plan, executor, teaching_skills, session, outcomes, etc. | No “active project” or “project goal stack” or “project blockers.” |
| **Teaching** | Skills (drafts, accepted, attached to packs). Stored under teaching/skill store. | No link from skill to project/case. |
| **Value packs / rollout / acceptance** | Reference sessions, jobs, runs for onboarding/demos. | No first-class project that owns those. |

So: we have **sessions**, **one current goal + latest plan**, **runs**, **outcomes**, and **artifacts** (via session and executor), but **no persistent project or case** that owns them, no **goal stack** (ordered goals, active vs deferred), and no **project-level state** (blocked / active / deferred / complete) or **recommended next project action**.

---

## 2. What is missing for a true project/case layer

- **Persistent project/case entity** — An explicit record (e.g. project_id, title, state, created_at, updated_at) that outlives a single session or run.
- **Project-scoped goal stack** — Ordered list of long-lived goals and subgoals per project, with status (active / deferred / complete / blocked) and optional dependency edges.
- **Links from project to existing entities** — Sessions, plans, runs, artifacts, outcomes, and (optionally) skills attached to a project so that “this project” has a clear history and current state.
- **Project state progression** — Track state over time (e.g. active, archived) and a notion of “current” or “active” project for the agent/operator.
- **Blocked dependency and next action** — Per-project view of what is blocked, why, and a recommended next project action (derived from goal stack + linked runs/plans).
- **Store and API** — Create/open/archive project; attach session/plan/run/artifact; update goal stack; query active goals and blockers; generate project report.

Without this, the system feels like isolated runs and sessions; with it, the agent can work in the context of a **long-lived project or case** and the planner/executor/teaching layers can later key off “current project” and “current goal stack.”

---

## 3. Exact file plan

| Phase | File | Purpose |
|-------|------|--------|
| **A** | `src/workflow_dataset/project_case/models.py` | Dataclasses: Project, Goal, Subgoal, ProjectMilestone, ProjectState, LinkedSession, LinkedPlan, LinkedRun, LinkedArtifact, LinkedSkill, BlockedDependency, NextProjectAction. |
| **B** | `src/workflow_dataset/project_case/store.py` | get_projects_dir, create_project, load_project, save_project, list_projects, set_current_project_id, get_current_project_id, archive_project; attach_session, attach_plan, attach_run, attach_artifact, attach_skill; update_project_state. |
| **B** | `src/workflow_dataset/project_case/graph.py` | Build project graph / summary from linked entities; query active goals and blockers. |
| **C** | `src/workflow_dataset/project_case/goal_stack.py` | Goal stack: add_goal, add_subgoal, set_goal_order, set_goal_status (active/deferred/complete/blocked), dependency edges, blocked_reason, recommended_next_goal. |
| **D** | `src/workflow_dataset/project_case/report.py` | format_project_list, format_project_show, format_goal_stack, format_project_report (summary + blockers + next action). |
| **D** | `src/workflow_dataset/project_case/__init__.py` | Exports for models, store, goal_stack, graph, report. |
| **D** | `src/workflow_dataset/cli.py` | Add `projects_group` and commands: list, create, show, goals, attach-session, attach-plan, attach-run, attach-artifact, report; optional set-current. |
| **D** | `src/workflow_dataset/mission_control/state.py` | Add `project_case` block: active_project_id, active_goal_stack_summary, project_blockers, latest_linked_plan/run/artifact, recommended_next_project_action. |
| **D** | `src/workflow_dataset/mission_control/report.py` | Add [Project / case] section when project_case present. |
| **E** | `tests/test_project_case_m27.py` | Tests: create/open/archive, goal stack ordering, attach session/plan/run, blocker reporting, project report. |
| **E** | `docs/M27A_M27D_PROJECT_CASE.md` | Doc: files, CLI, sample record, goal stack output, report, tests, gaps. |

Storage: `data/local/project_case/` — `projects/` (one dir or file per project), `current_project_id.json`, and within each project a `project.json` (metadata + state) and `goals.json` (goal stack + dependencies).

---

## 4. Safety / risk note

- **Read-only integration** — Project layer will **read** sessions, planner store, executor hub, outcomes to build summaries and links; it will **not** modify those subsystems. Attachments are stored as references (ids/paths) in project_case store only.
- **No auto-switching** — Setting “current project” is explicit (CLI or future UI). No hidden autonomous project creation or goal changes.
- **Local only** — All state under `data/local/project_case/`. No cloud sync or hidden network.
- **Conflict with existing “project”** — CLI and `personal/project_interpreter` use “project” in a different sense (e.g. codebase/directory projects). We use a dedicated `projects` command group and `project_case` package to avoid name clashes; mission_control key is `project_case`.

---

## 5. What this block will NOT do

- **Multi-user or team collaboration** — Single-operator, local-first only.
- **Cloud project sync or PM SaaS** — No Jira/Linear/Notion integration; no hidden sync.
- **Autonomous project or goal mutation** — No background updates to project state or goal stack; all changes are explicit (CLI or future explicit API).
- **Rebuild of sessions/outcomes/planner/executor** — We only reference them by id/path and optionally show linked data in reports.
- **Full dependency solver** — Goal dependencies are stored and displayed; we do not implement a full constraint solver or auto-ordering.

---

Once this is agreed, implementation proceeds: Phase A (models) → Phase B (store + graph) → Phase C (goal stack) → Phase D (CLI + mission control) → Phase E (tests + docs).

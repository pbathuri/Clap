# Pilot operator guide (M20)

How to prepare a pilot user, verify readiness, run the narrow pilot flow, diagnose common failures, and decide whether to continue or pause.

---

## 1. Preparing a pilot user

- **Profile:** Per docs/PILOT_SCOPE.md — one person doing recurring reporting/status work (ops); single device; local-first.
- **Before the session:** Share the trial kit (docs/trial/) and PILOT_SCOPE.md so they know what is in and out of scope.
- **One-time setup:** Either you (on their machine) or they run: environment + `workflow-dataset pilot verify`. If verify fails, fix blocking issues (graph, setup) before the pilot session.

---

## 2. Verifying readiness before a session

Run from the project root (directory containing `configs/`) or use absolute paths. Relative config paths are resolved against project root:

```bash
workflow-dataset pilot verify --config configs/settings.yaml --release-config configs/release_narrow.yaml
```

- **Exit 0:** Ready. You may see warnings (e.g. no adapter → degraded mode); document in session.
- **Exit 1:** Blocking issues (e.g. graph missing, setup missing). Do not start the pilot until resolved.

Optional:

```bash
workflow-dataset pilot status
```

Use this to confirm: ready, safe-to-demo, degraded (no adapter), and path to latest feedback report.

---

## 3. Running the narrow pilot flow

### Grounded pilot session (recommended)

For higher-quality evidence and demo outputs that reflect real workflow context:

- **Before the run:** Execute `setup init` and `setup run` so the graph has projects and style signals. For grounded demo: use `release demo --retrieval` when corpus exists, and/or pass task-scoped context with `--context-file path/to/context.txt` or `--context-text "e.g. weekly ops reporting for project delivery"` (local-only; see docs/FOUNDER_DEMO_FLOW.md).
- **Recognizing weak grounding:** If the CLI shows **Retrieval relevance: weak** or **mixed**, the model is instructed to qualify its answer; do not treat the output as confident. Use explicit task context to anchor the run when retrieval is often weak. After the run, check `data/local/pilot/last_demo_grounding.txt` and `last_retrieval_relevance.txt` for session notes.
- **Output location:** Use `release demo [--workflow WORKFLOW] --save-artifact` to write to the workflow sandbox. **Ops reporting suite:** `--workflow weekly_status` (default) | `status_action_bundle` | `stakeholder_update_bundle` | `meeting_brief_bundle` | `ops_reporting_workspace`. Paths: `data/local/workspaces/weekly_status/`, `data/local/workspaces/status_action_bundle/`, `data/local/workspaces/stakeholder_update_bundle/`, `data/local/workspaces/meeting_brief_bundle/`, `data/local/workspaces/ops_reporting_workspace/`. For `ops_reporting_workspace`, each run creates a timestamped subdir with workspace_manifest.json, source_snapshot.md, and artifact .md files. The CLI prints the exact path. Without `--save-artifact`, output is terminal-only. See docs/FOUNDER_DEMO_FLOW.md.
- **In end-session notes:** Note whether the run was grounded (e.g. "Grounded: task context + retrieval" or "Ungrounded") and, if retrieval was used, the relevance (high/mixed/weak). Without grounded context, demo outputs may be generic.

### M21 batch execution (session-level evidence)

For structured session and feedback evidence used in aggregate reports and the readiness report:

1. **Verify:** `workflow-dataset pilot verify`
2. **Start session:** `workflow-dataset pilot start-session --operator <name> --scope ops`
3. **Run flow:** `workflow-dataset release run` and/or `workflow-dataset release demo [--workflow weekly_status|status_action_bundle|stakeholder_update_bundle|meeting_brief_bundle|ops_reporting_workspace]` (for demo, if the default LLM config is missing, pass `--llm-config configs/llm_training_full.yaml`). Use `--save-artifact` to write to the workflow sandbox. For `ops_reporting_workspace`, use `--context-file` and/or `--context-text` and optionally `--retrieval` for a full multi-artifact workspace. For context-grounded demo, run setup first and use `release demo --retrieval` when corpus exists (see docs/FOUNDER_DEMO_FLOW.md).
4. **Capture feedback:** `workflow-dataset pilot capture-feedback --usefulness 1-5 --trust 1-5 --adoption 1-5` (and optional `--friction`, `--user-quote`, `--notes`, `--next-steps-specific yes|no`, `--report-location-clear yes|no`). For **status_action_bundle** use `--status-brief-send-ready`, `--action-register-usable`; for **stakeholder_update_bundle** use `--stakeholder-update-send-ready`, `--decision-requests-usable`; for **meeting_brief_bundle** use `--meeting-brief-send-ready`, `--action-items-usable`. **Structured evidence:** Aggregate counts only `--user-quote` and `--friction`. Always add at least one `--user-quote` and one `--friction` for evidence quality.
5. **End session:** `workflow-dataset pilot end-session --notes "..." --disposition continue|fix|pause`
6. **Aggregate:** `workflow-dataset pilot aggregate`
7. **Report:** `workflow-dataset pilot latest-report` to refresh pilot_readiness_report.md (includes M21 session/feedback counts)

See **docs/PILOT_RUNBOOK.md** for the exact command sequence and paths.

### Operator review queue (M21T)

After saving artifacts with `release demo --save-artifact`, you can inspect, approve, and package them for handoff:

1. **List workspaces:** `workflow-dataset review list-workspaces` — shows recent runs under `data/local/workspaces/` (weekly_status, bundles, ops_reporting_workspace).
2. **Inspect one:** `workflow-dataset review show-workspace <path-or-id>` — e.g. `review show-workspace ops_reporting_workspace/2025-03-15_1432_abc` or full path. Shows workflow, artifacts, and current review state per artifact.
3. **Approve artifacts:** `workflow-dataset review approve-artifact <workspace> --artifact weekly_status.md` (repeat for each artifact to include). Use `review set-artifact-state <workspace> --artifact x --state needs_revision|excluded` to mark others.
4. **Build package:** `workflow-dataset review build-package <workspace>` — writes to `data/local/packages/<ts_id>/` with approved artifacts only, plus `package_manifest.json`, `approved_summary.md`, `handoff_readme.md`. No apply; sandbox-only. **Handoff profiles (B3):** `--profile internal_team` (default), `--profile stakeholder` (stakeholder-facing only), or `--profile operator_archive` (full set for audit). List: `workflow-dataset review list-profiles`.
5. **Package status:** `workflow-dataset review package-status <workspace>` — shows approved count and last built package path.
6. **Review metrics (B4):** `workflow-dataset review metrics` — read-only summary: pending review count, revision rate, avg approved per workspace/package, common revision reasons. Use `--json` for machine output.
8. **Apply (optional):** To copy the package to a target dir, use the existing apply flow: `workflow-dataset assist apply-plan <package_dir> <target_path>` then `workflow-dataset assist apply <package_dir> <target_path> --confirm`. No automatic apply.

**Staging board (M21V):** Before apply, you can queue approved packages/artifacts on a staging board, then build an apply-plan preview without applying. Commands: `workflow-dataset review queue-status` (review + staging summary), `review stage-package <package_path>`, `review stage-artifact <workspace> --artifact <name>`, `review staging-board` (list staged items), `review unstage --item <id>`, `review clear-staging`, `review build-apply-plan <target_path>` (preview only; no apply), `review apply-plan-status`. State: `data/local/staging/staging_board.json`; last preview: `data/local/staging/last_apply_plan_preview.md`. Apply still requires explicit `assist apply ... --confirm`.

Review state is stored under `data/local/review/<workflow>/<run_id>.json`. Packages are under `data/local/packages/`.

### Local Reporting Command Center (M21U + C2)

One place to see readiness, recent workspaces, review/package queue, cohort, and next actions:

- **CLI:** `workflow-dataset dashboard` — prints the full dashboard (readiness, workspaces, review & package counts, cohort recommendation, recommended next commands with exact paths). No prompt; safe to run from scripts.
- **Workflow filter (C2):** `workflow-dataset dashboard --workflow <name>` — limit views to one workflow (e.g. `weekly_status`, `status_action_bundle`, `stakeholder_update_bundle`, `ops_reporting_workspace`). Counts and recent workspaces are filtered accordingly.
- **Drill-downs (C2):** From the dashboard you can inspect a single “latest” item:
  - `workflow-dataset dashboard workspace` — latest workspace detail (path, artifacts, approved, inspect/build commands). Optional `--workflow` to filter.
  - `workflow-dataset dashboard package` — latest package dir (path, files, open command).
  - `workflow-dataset dashboard cohort` — latest cohort report (path, excerpt, open command).
  - `workflow-dataset dashboard apply-plan` — latest apply-plan preview (path, excerpt, open command).
- **Console:** From the operator console home menu, press **D** (Dashboard). Then use **W** (workspace), **P** (package), **C** (cohort), **A** (apply-plan) to open a drill-down, or Enter to return to home.
- **Action shortcuts (C4):** Run a macro from the dashboard: `workflow-dataset dashboard action <id>` with id `inspect-workspace`, `open-package`, `open-cohort-report`, `staging-board`, or `benchmark-board`. In console, press **1**–**5** to run the 1st–5th shortcut. Commands are shown; no hidden automation.

**Grouping:** Readiness, workspaces & review, packages & staging, cohort state, and next actions are grouped with clear section headers. **Panel 6 — Local sources (provenance):** Exact local paths used: `repo_root`, `workspaces_root`, `pilot_dir`, `packages_root`, `review_root`, `staging_dir`, and when present `pilot_readiness_report`, `release_readiness_report`. Next-action commands use concrete workspace refs and artifact names so you can copy-paste. Sources are local only; no writes.

### Trial flow (task-level)

1. **Start trial session:** `workflow-dataset trial start --user <alias>`
2. **Run flow:** Either:
   - `workflow-dataset release run` — runs ops trials (adapter or base model)
   - `workflow-dataset release demo` — 3 prompts (founder demo)
3. If you see **Degraded mode: no adapter** — expected when LLM has not been trained; base model is used. Note it in feedback.
4. **Record feedback:** `workflow-dataset trial record-feedback <task_id> --outcome completed|partial|failed --usefulness 1-5 --trust 1-5 -f "notes"`
5. **End session:** `workflow-dataset trial summary` then optionally `workflow-dataset trial aggregate-feedback`
6. **Pilot report:** `workflow-dataset pilot latest-report` to refresh pilot_readiness_report.md

---

## 4. Diagnosing the most common failures

| Symptom | Likely cause | Action |
|--------|---------------|--------|
| `pilot verify` exit 1 | Graph missing or setup dirs missing | Run `setup init` and `setup run`; re-check config paths. |
| "LLM adapter: missing" | No successful training run | Use degraded mode (base model) or run LLM train and re-verify. |
| "Degraded mode: no adapter" during run/demo | Same as above | Expected; continue with base model or train adapter. |
| Inference error / crash during demo | Backend or model load failure | Check LLM config (base_model, backend); try without adapter. Run `pilot record-blocking "description"` then `pilot end-session --disposition fix` so the session reflects the failure. |
| Empty suggestions in console | Sparse graph or no style signals | Expected in some setups; document in feedback. |
| Retrieval failed | Corpus missing or path wrong | Demo/run continue without retrieval; optional. |

Use **docs/RELIABILITY_TRIAGE.md** and **data/local/pilot/reliability_issues.json** for the full triage list.

---

## 5. When to stop the session and log a failure

- **Stop and log:** User cannot complete pilot verify after following setup docs; or a command (e.g. `release demo`) crashes during the session; or repeated inference crash with no workaround; or any uncontrolled write or data loss.
- **Record the failure in the pilot session** so aggregate/reporting is honest:
  1. Run `workflow-dataset pilot record-blocking "short description"` (e.g. `pilot record-blocking "release demo crashed: UnboundLocalError llm_cfg"`). Uses current session; or pass `--session-id` if needed.
  2. Optionally run `pilot capture-feedback` with `--blocker` and `--failure-reason "..."` so feedback reflects the failure.
  3. Run `pilot end-session --disposition fix` or `--disposition pause` so the aggregate and readiness report show the blocking issue and disposition.
- **Blocking vs friction:** **Blocking** = command crash, flow cannot complete, or critical failure — use `pilot record-blocking` and disposition fix/pause. **Friction** = UX/docs annoyance (e.g. report location unclear) — use `pilot capture-feedback --friction "..."` and disposition can remain continue.
- **Run** `pilot aggregate` and `pilot latest-report` so the next decision has evidence.

---

## 6. When to trust outputs vs keep assist-only

- **Assist-only (no apply):** Default for pilot. Suggestions and generated text are for review; do not run apply to real project paths unless the user explicitly requests and you have confirmed preview.
- **Trust to adopt:** If the user rates usefulness/trust ≥ 3 and freeform says they would use the suggestion, they may choose to run apply preview then confirm. Ensure they understand apply is opt-in and sandbox-first.

---

## 7. Deciding whether the pilot should continue, pause, or roll back scope

- **Continue:** pilot verify passes; feedback shows usefulness/trust ≥ 3 and no critical blockers. Add another pilot user per PILOT_SCOPE (2–5 users total).
- **Pause:** Recurring failure (e.g. verify never passes on a machine, or inference always fails). Fix blocking issues; do not add more users until stable.
- **Roll back scope:** If users consistently try out-of-scope workflows (e.g. spreadsheet, creative) and are confused, reinforce scope in docs and operator prep; do not add those workflows yet.

Use **data/local/pilot/pilot_readiness_report.md** and **data/local/trials/latest_feedback_report.md** for the written recommendation.

---

## 8. Fresh cohort evaluation and graduation readiness (M21O)

To decide whether the narrow pilot should **continue unchanged**, **refine one focused issue**, or **graduate to a broader controlled pilot cohort**, use a **recent cohort** (rolling window) so the decision is based on current evidence, not only cumulative historical counts.

### Run a fresh evaluation cohort

1. **Aggregate with recent-cohort and graduation:**  
   `workflow-dataset pilot aggregate [--recent 5]`  
   When you have at least 5 sessions (or the number you pass to `--recent`), the report includes:
   - **All sessions (cumulative)** — full history.
   - **Recent cohort (last N sessions)** — counts and evidence for the most recent N sessions only.
   - **Graduation readiness** — criteria pass/fail and recommendation (continue / refine_once / graduate).

2. **Quick graduation check only:**  
   `workflow-dataset pilot graduation-status [--recent 5]`  
   Prints the recommendation and criteria for the last N sessions without writing the full report.

### Where to read the result

- **Markdown:** Open `data/local/pilot/aggregate_report.md` and scroll to **Recent cohort** and **Graduation readiness**.
- **JSON:** In `data/local/pilot/aggregate_report.json`, see `recent_cohort` (aggregate for last N sessions) and `graduation` (criteria_checks, recommendation_grade, summary).

### How to decide

- **Recommendation = graduate** — Recent cohort meets all graduation criteria; consider expanding to a broader controlled pilot cohort.
- **Recommendation = refine_once** — One criterion failed in the recent cohort; fix that issue, run more sessions, then re-run `pilot aggregate --recent N` or `pilot graduation-status` to re-check.
- **Recommendation = continue** — Two or more criteria failed; keep running the narrow pilot and re-evaluate with a fresh cohort after more sessions.

Graduation criteria are listed in **docs/M21_PILOT_EXECUTION.md** (Narrow-pilot graduation criteria).

**Structured yes/no for graduation (M21P):** Use `--next-steps-specific yes` or `no` and `--report-location-clear yes` or `no` when capturing feedback. These structured fields drive the **concerns_low** graduation criterion; freeform notes and friction text are still useful but are treated as inferred (advisory) and do not override explicit structured answers. Old feedback that had "Next steps specific enough: yes" (or no) in freeform notes is parsed for backward compatibility and counts as structured when present.

---

## 9. Broader controlled pilot cohort (M21Q)

After the narrow pilot has graduated, you can run a **broader controlled pilot cohort** (same ops/reporting scope, 2–5 operators):

- **Cohort tracking:** Start every session in the batch with `--cohort <cohort_id>` (e.g. `broader_2026_q1`). Only sessions with that cohort_id are included in the cohort report.
- **Commands:** `pilot start-session --cohort <id>`, then run/demo and capture-feedback as usual. When the batch is done: `pilot cohort-status --cohort <id>` for a quick outcome, or `pilot cohort-report --cohort <id>` to write the full cohort report.
- **Outcome rubric:** continue_within_scope | expand_adjacent | hold_refine | rollback (see cohort report and **docs/BROADER_PILOT_RUNBOOK.md**).

Full runbook: **docs/BROADER_PILOT_RUNBOOK.md** (preflight, session flow, feedback and artifact expectations, evaluation cadence).

---

## 10. Desktop bridge (M23H)

The desktop bridge exposes **adapters** (file_ops, notes_document, browser_open, app_launch), **capability discovery**, **approvals**, **task demos**, and **coordination graph** in a local-first, simulate-first, approval-gated way.

### Verifying the desktop bridge

Run these from the project root (or with `--repo-root <path>` where needed):

- **Adapters:** `workflow-dataset adapters list` — lists adapters with simulate/real_execution flags.
- **Capabilities:** `workflow-dataset capabilities scan` — adapter count, approved_paths/apps/scopes (from registry if present).
- **Approvals:** `workflow-dataset approvals list` — path to `data/local/capability_discovery/approvals.yaml` and current approved_paths / approved_action_scopes.
- **Tasks:** `workflow-dataset tasks list` — task demo IDs; `workflow-dataset tasks show <id>` for detail.
- **Graph:** `workflow-dataset graph summary` — coordination graph summary (tasks, nodes, edges).
- **Mission control:** `workflow-dataset mission-control` (or dashboard) — includes **[Desktop bridge]** (adapters, approvals present/missing, task demos, graph) and may recommend **replay_task** when task demos exist.

### What is simulate-only vs real execution

- **Simulate-only (no real execution):** `browser_open`, `app_launch`; task replay (`tasks replay`) uses simulate only. Safe to run without approvals.
- **Real execution (gated):** `file_ops` (inspect_path, list_directory, snapshot_to_sandbox) and `notes_document` (read_text, summarize_text_for_workflow, propose_status_from_notes). These are read-only or copy-to-sandbox only. They are **gated** when an approval registry exists.

### Enabling safe approved real execution

1. **No registry:** If `data/local/capability_discovery/approvals.yaml` does not exist, all real-execution actions above are allowed (backward compatible).
2. **With registry:** Create or edit `data/local/capability_discovery/approvals.yaml`:
   - **approved_paths:** List path prefixes allowed for path-using actions (e.g. `/tmp/safe`, `data/local`). Empty = no path restriction.
   - **approved_action_scopes:** List `{adapter_id, action_id, executable: true}` for actions you allow. If this list is non-empty, only listed actions can run; others are refused with a clear message.
3. **Run real actions:** `workflow-dataset adapters run --id file_ops --action inspect_path --param path=/allowed/path [--repo-root .]`. If approval is missing, the CLI prints a refusal message (e.g. "Path not in approved_paths" or "Action not in approved_action_scopes").
4. **Sandbox:** `snapshot_to_sandbox` always writes under the sandbox root (default `data/local/desktop_adapters/sandbox`); it does not mutate the source path.

See **docs/M23H_DESKTOP_BRIDGE_OPERATOR.md** for the full operator smoke and approval reference.

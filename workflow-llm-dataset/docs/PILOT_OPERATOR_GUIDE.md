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
- **Output location:** Use `release demo --save-artifact` to write the weekly status to **data/local/workspaces/weekly_status/** (sandbox); the CLI prints the exact path. Without the flag, output is terminal-only.
- **In end-session notes:** Note whether the run was grounded (e.g. "Grounded: task context + retrieval" or "Ungrounded") and, if retrieval was used, the relevance (high/mixed/weak). Without grounded context, demo outputs may be generic.

### M21 batch execution (session-level evidence)

For structured session and feedback evidence used in aggregate reports and the readiness report:

1. **Verify:** `workflow-dataset pilot verify`
2. **Start session:** `workflow-dataset pilot start-session --operator <name> --scope ops`
3. **Run flow:** `workflow-dataset release run` and/or `workflow-dataset release demo` (for demo, if the default LLM config is missing, pass `--llm-config configs/llm_training_full.yaml`). For context-grounded demo outputs, run setup first and use `release demo --retrieval` when corpus exists; without context, outputs may be generic (see docs/FOUNDER_DEMO_FLOW.md).
4. **Capture feedback:** `workflow-dataset pilot capture-feedback --usefulness 1-5 --trust 1-5 --adoption 1-5` (and optional `--friction`, `--user-quote`, `--notes`, `--next-steps-specific yes|no`, `--report-location-clear yes|no`). **Structured evidence:** Aggregate counts only `--user-quote` and `--friction`; freeform notes are not parsed as quotes/friction. Always add at least one `--user-quote` and one `--friction` for evidence quality. Use `--next-steps-specific` and `--report-location-clear` when relevant.
5. **End session:** `workflow-dataset pilot end-session --notes "..." --disposition continue|fix|pause`
6. **Aggregate:** `workflow-dataset pilot aggregate`
7. **Report:** `workflow-dataset pilot latest-report` to refresh pilot_readiness_report.md (includes M21 session/feedback counts)

See **docs/PILOT_RUNBOOK.md** for the exact command sequence and paths.

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

# Pilot operator guide (M20)

How to prepare a pilot user, verify readiness, run the narrow pilot flow, diagnose common failures, and decide whether to continue or pause.

---

## 1. Preparing a pilot user

- **Profile:** Per docs/PILOT_SCOPE.md — one person doing recurring reporting/status work (ops); single device; local-first.
- **Before the session:** Share the trial kit (docs/trial/) and PILOT_SCOPE.md so they know what is in and out of scope.
- **One-time setup:** Either you (on their machine) or they run: environment + `workflow-dataset pilot verify`. If verify fails, fix blocking issues (graph, setup) before the pilot session.

---

## 2. Verifying readiness before a session

Run:

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
| Inference error / crash during demo | Backend or model load failure | Check LLM config (base_model, backend); try without adapter. |
| Empty suggestions in console | Sparse graph or no style signals | Expected in some setups; document in feedback. |
| Retrieval failed | Corpus missing or path wrong | Demo/run continue without retrieval; optional. |

Use **docs/RELIABILITY_TRIAGE.md** and **data/local/pilot/reliability_issues.json** for the full triage list.

---

## 5. When to stop the session and log a failure

- **Stop and log:** User cannot complete pilot verify after following setup docs; or repeated inference crash with no workaround; or any uncontrolled write or data loss.
- **Record feedback** with outcome `failed` and freeform describing the blocker.
- **Run** `trial summary` and `pilot latest-report` so the next decision has evidence.

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

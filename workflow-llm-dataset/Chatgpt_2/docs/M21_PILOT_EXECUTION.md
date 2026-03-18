# M21 — Pilot execution and iteration

What this milestone adds: session tracking, structured feedback capture, aggregation across sessions, and clearer operator flow — without broadening scope or adding cloud/remote backends.

---

## What was added

1. **Pilot session tracking** — Start and end sessions locally; record operator, scope, task type, config, adapter/degraded mode, commands run, blocking issues, warnings, notes, disposition (continue / fix / pause). Persisted under `data/local/pilot/sessions/`.
2. **Structured feedback capture** — Per-session feedback: usefulness, trust, clarity, adoption likelihood (1–5), blocker yes/no, top failure reason, operator friction, user quote, freeform notes. Stored under `data/local/pilot/feedback/`.
3. **Pilot aggregation** — Combine session logs and feedback into: recurring blockers, warning frequency, degraded-mode frequency, disposition counts, operator friction excerpts, user quotes, average usefulness, recommendation summary. Output: `aggregate_report.json` and `aggregate_report.md`.
4. **CLI** — `pilot start-session`, `pilot end-session`, `pilot capture-feedback`, `pilot aggregate`, `pilot latest-summary`. Existing `pilot verify`, `pilot status`, `pilot latest-report` unchanged.
5. **Console** — Pilot view shows latest session, aggregate findings (session count, degraded count, recurring blockers, recommendation), and CLI hints for session/feedback/aggregate.
6. **Presentability** — Degraded-mode wording clarified; operator next-step clarity improved.

---

## How to run pilot sessions

1. **Verify readiness**  
   `workflow-dataset pilot verify`  
   Config paths are resolved from project root (directory containing `configs/settings.yaml`), so this works from any cwd. Exit 1 if blocking; fix before starting a session.

2. **Start a session**  
   `workflow-dataset pilot start-session [--operator NAME] [--scope ops]`  
   Creates a session record and sets it as current. Degraded state (no adapter) is recorded if present.

3. **Run the narrow flow**  
   e.g. `workflow-dataset release run` or `workflow-dataset release demo`.  
   If you see degraded-mode notices, they reflect the current state; document in session notes or feedback.

4. **Capture feedback**  
   `workflow-dataset pilot capture-feedback --usefulness 4 --trust 3 --adoption 4 [--blocker] [--notes "..."]`  
   Uses current session unless `--session-id` is set.

5. **End the session**  
   `workflow-dataset pilot end-session [--notes "..."] [--disposition continue|fix|pause]`  
   Finalizes the session and clears “current session”.

6. **Aggregate (after one or more sessions)**  
   `workflow-dataset pilot aggregate`  
   Writes `data/local/pilot/aggregate_report.json` and `aggregate_report.md`.

7. **Latest summary**  
   `workflow-dataset pilot latest-summary`  
   Prints the most recent session and its feedback (if any).

---

## How to capture feedback

Use `pilot capture-feedback` with optional flags:

- `--usefulness` / `-u` 1–5  
- `--trust` / `-t` 1–5  
- `--clarity` / `-c` 1–5  
- `--adoption` / `-a` 1–5 (would use again)  
- `--blocker` if a critical blocker was encountered  
- `--failure-reason` / `-f` short reason  
- `--friction` operator friction notes  
- `--user-quote` / `-q` user quote  
- `--notes` / `-n` freeform notes  

Stored as `data/local/pilot/feedback/<session_id>_feedback.json`. Schema: see **docs/PILOT_FEEDBACK_SCHEMA.md**.

---

## How to aggregate evidence

- **Command:** `workflow-dataset pilot aggregate [--pilot-dir data/local/pilot] [--limit 100]`  
- **Inputs:** All (or recent, by `--limit`) session JSON files under `data/local/pilot/sessions/` and feedback files under `data/local/pilot/feedback/`.  
- **Outputs:**  
  - `data/local/pilot/aggregate_report.json` — machine-readable (recurring_blockers, warning_counts, degraded_count, disposition_counts, recommendation_summary, session_summaries, feedback_by_session, etc.).  
  - `data/local/pilot/aggregate_report.md` — human-readable summary and recommendation.

Aggregation is deterministic from existing session and feedback files; no network or LLM.

---

## What remains out of scope

- Multi-agent orchestration, connector expansion, cloud/provider backends.  
- Broad workflow automation or public-release expansion.  
- Any change to materialize/apply safety gates or local-only persistence.  
- Telemetry or remote submission of pilot data.

---

## Criteria: continue / refine / pause

- **Continue pilot** — No recurring blocking issues; at least one of usefulness ≥ 3, trust ≥ 3, or freeform “adoptable”; no critical blocker (uncontrolled write, data loss); operator can resolve issues via pilot docs and status.  
- **Refine and re-pilot** — Recurring blockers or repeated degraded mode; fix (e.g. graph, setup, adapter) then run another session batch and re-aggregate.  
- **Pause** — Repeated verify failure; repeated inference failure with no fallback; user-reported uncontrolled write or data loss; or operator cannot resolve blocking issues with pilot docs and commands. Use disposition `pause` in end-session and address before next batch.

Evidence for the decision comes from session logs, structured feedback, and the aggregate report — all local and inspectable.

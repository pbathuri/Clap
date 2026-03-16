# Pilot runbook (M21 batch execution)

One-page sequence to run a narrow pilot batch and capture evidence. All commands are repo-local; no cloud or remote submission.

---

## Prerequisites

- Environment set up; `workflow-dataset` on PATH (or run from project root: `cd workflow-llm-dataset` then `python -m workflow_dataset`).
- Config present under project root: `configs/settings.yaml`, `configs/release_narrow.yaml`.
- **Config paths:** Relative paths (e.g. `configs/settings.yaml`) are resolved against the **project root** (directory containing `configs/settings.yaml`).
- **Working directory:** Run commands from the **project root** (`workflow-llm-dataset`) so that config and data paths (e.g. `data/local/`) resolve correctly.

---

## 1. Verify readiness

```bash
workflow-dataset pilot verify --config configs/settings.yaml --release-config configs/release_narrow.yaml
```

- **Exit 0:** Proceed. Warnings (e.g. no adapter → degraded) are acceptable; they will be recorded in the session.
- **Exit 1:** Fix blocking issues (e.g. graph, setup dirs) before starting a session.

---

## 2. Start a pilot session

```bash
workflow-dataset pilot start-session --operator "YourName" --scope ops
```

Optional: `--task-type`, `--config`, `--release-config`, `--pilot-dir` (default `data/local/pilot`).

- Creates a session under `data/local/pilot/sessions/pilot_<date>_<time>_<id>.json`.
- Sets current session in `data/local/pilot/current_session.json`.
- Degraded mode (no adapter) is recorded automatically from verify state.

---

## 2b. Grounded session (recommended for quality evidence)

For demo outputs that reflect real workflow context (not generic):

1. **Run setup** so the graph has projects and style signals: `workflow-dataset setup init` and `workflow-dataset setup run` (with a scan root that has sample files).
2. **Optional:** Prepare corpus (`workflow-dataset llm prepare-corpus`) and use `workflow-dataset release demo --retrieval` when `data/local/llm/corpus/corpus.jsonl` exists.
3. In **end-session notes**, note whether the run was grounded (e.g. "Grounded: setup run + demo" or "Ungrounded: no corpus"). If you used `--retrieval`, the CLI shows **Retrieval relevance: high | mixed | weak** per prompt and writes the run’s relevance to `data/local/pilot/last_retrieval_relevance.txt`; you can note it in session notes (e.g. "retrieval relevance: weak") for evidence quality.

Without grounded context, demo outputs may be generic; the aggregate report can still use the session but will reflect this.

---

## 3. Run the narrow flow

Choose one or both:

```bash
workflow-dataset release run
```

and/or

```bash
workflow-dataset release demo
```

- `release run`: runs ops trials (adapter or base model).
- `release demo`: 3 founder-demo prompts. **Requires** an LLM config with `base_model`; if the default is not found, run with `--llm-config configs/llm_training_full.yaml` (or `configs/llm_training.yaml`). Paths are resolved from project root.
- If you see "Degraded mode: no adapter", note it in session notes or feedback.

---

## 4. Capture structured feedback

```bash
workflow-dataset pilot capture-feedback --usefulness 4 --trust 3 --adoption 4
```

Optional: `--clarity`, `--blocker`, `--failure-reason`, `--friction`, `--user-quote`, `--notes`, `--next-steps-specific yes|no`, `--report-location-clear yes|no`, `--session-id` (if not using current).

- Writes `data/local/pilot/feedback/<session_id>_feedback.json`.
- Uses current session unless `--session-id` is set.
- **Structured evidence (first-class):** Aggregate counts **only** `--user-quote` and `--friction`. Freeform `--notes` are not parsed as quotes or friction. Always pass at least one `--user-quote` and one `--friction` for meaningful evidence counts. Use `--next-steps-specific` and `--report-location-clear` (yes/no) when relevant; these are appended to notes for concern-pattern counts.

---

## 5. End the session

```bash
workflow-dataset pilot end-session --notes "Brief operator notes" --disposition continue
```

- Disposition: `continue` | `fix` | `pause`.
- Finalizes the session and clears current session.

---

## 6. Aggregate evidence (after one or more sessions)

```bash
workflow-dataset pilot aggregate
```

Optional: `--pilot-dir data/local/pilot`, `--limit 100`.

- Writes:
  - `data/local/pilot/aggregate_report.json`
  - `data/local/pilot/aggregate_report.md`

---

## 7. Inspect summary and report

```bash
workflow-dataset pilot latest-summary
workflow-dataset pilot latest-report
```

- **latest-summary:** Prints latest session and its feedback (if any).
- **latest-report:** Regenerates `data/local/pilot/pilot_readiness_report.md` (includes M21 session/feedback counts).

---

## Paths (defaults)

| What            | Path |
|-----------------|------|
| Pilot root      | `data/local/pilot` |
| Sessions        | `data/local/pilot/sessions/*.json` |
| Current session | `data/local/pilot/current_session.json` |
| Feedback        | `data/local/pilot/feedback/<session_id>_feedback.json` |
| Aggregate       | `data/local/pilot/aggregate_report.json`, `aggregate_report.md` |
| Readiness report| `data/local/pilot/pilot_readiness_report.md` |

---

## When there is no evidence yet

- **Pilot sessions completed: 0** and **Structured feedback entries: 0** in the readiness report means no M21 sessions have been run. Follow steps 1–6 above to generate evidence, then run `pilot latest-report` and review `aggregate_report.md` for the decision memo inputs.

---

## References

- **M21 flow:** docs/M21_PILOT_EXECUTION.md  
- **Feedback schema:** docs/PILOT_FEEDBACK_SCHEMA.md  
- **Operator guide:** docs/PILOT_OPERATOR_GUIDE.md  
- **Scope:** docs/PILOT_SCOPE.md  

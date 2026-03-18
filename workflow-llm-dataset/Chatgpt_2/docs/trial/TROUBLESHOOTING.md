# Trial troubleshooting

Common issues and what to do.

---

## “Graph not found” or “Graph: missing”

- **Cause:** Setup has not been run, or the graph file path is wrong.
- **Fix:** Run `workflow-dataset setup init` (if needed) and `workflow-dataset setup run` so that the graph and parsed artifacts are created. Then run `workflow-dataset release verify` again.
- **Trial impact:** You can still run some commands (e.g. `llm demo` with a prompt), but suggestions and context will be minimal. Record that setup was missing in your feedback.

---

## “LLM adapter: missing”

- **Cause:** No trained adapter has been produced yet (no `llm train` or `llm smoke-train`).
- **Fix:** Optional. The system can run with the base model or baseline behavior; outputs may be more generic. If the operator has provided an adapter path, ensure the release config points to the correct LLM config and that the adapter dir exists under `data/local/llm/runs`.
- **Trial impact:** Note in feedback that you ran “without adapter” so we know the baseline experience.

---

## “No trial results found” or “No trial tasks”

- **Cause:** Trial tasks or results are expected under `data/local/trials` but the dir is empty or the task set wasn’t loaded.
- **Fix:** Run `workflow-dataset trial start` to ensure a session exists. Run `workflow-dataset trial tasks` to list tasks. Run `workflow-dataset release run` or individual `trials run <task_id>` to produce results. If the feedback store is empty, that’s normal before you run `trial record-feedback`.
- **Trial impact:** Continue with the quickstart; record feedback after each task.

---

## Command not found: workflow-dataset

- **Cause:** The CLI isn’t on your PATH or you’re not in the right environment.
- **Fix:** Activate the project’s virtual environment (e.g. `. .venv/bin/activate` on macOS/Linux) and run from the project root. Use `python -m workflow_dataset.cli` if the `workflow-dataset` entry point isn’t installed.
- **Trial impact:** Ask the operator for the exact activate and run commands for your OS.

---

## Demo or run produces “inference error” or empty output

- **Cause:** LLM backend (e.g. MLX) failed: missing model, out of memory, or timeout.
- **Fix:** Check that the base model is available (see `llm verify`). On low memory, try closing other apps. If the error persists, record the exact command and error message in feedback.
- **Trial impact:** Record outcome “failed” and paste the error in freeform feedback so we can fix or document it.

---

## Console shows “No sessions” or empty lists

- **Cause:** No setup session exists, or graph/setup dirs are empty.
- **Fix:** Run setup (init + run) so at least one session and some parsed artifacts exist. Then reopen the console.
- **Trial impact:** You can still use the CLI for demo and trial tasks; note “console empty” in feedback.

---

## I want to report a bug or suggest a feature

- **How:** Use `workflow-dataset trial record-feedback` with freeform text, or send the contents of your session summary file to the trial operator. Include: what you ran, what you expected, what happened, and (if applicable) your session id.
- **Where:** Feedback is stored locally; the operator may ask you to share the relevant file or paste the summary. We do not have automatic bug reporting; it’s manual and local-first.

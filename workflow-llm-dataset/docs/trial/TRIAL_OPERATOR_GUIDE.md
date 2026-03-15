# Trial operator guide (M19)

This guide is for the founder/operator who prepares and runs friendly-user trials. The goal is to get honest, structured feedback without over-directing the user.

---

## 1. Preparing a trial user

- **Who:** Someone who does recurring reporting or status work (ops) and is willing to try a narrow tool without expecting a full product.
- **Before the trial:** Send them the trial kit:
  - `docs/trial/FRIENDLY_TRIAL_OVERVIEW.md`
  - `docs/trial/TRIAL_QUICKSTART.md`
  - `docs/trial/TRIAL_EXPECTATIONS.md`
  - `docs/trial/TRIAL_BOUNDARIES_AND_PRIVACY.md`
  - `docs/trial/TRIAL_TASKS.md`
- **One-time setup:** They (or you, on their machine) run:
  - Environment setup (Python, repo, configs)
  - `workflow-dataset release verify`
  - `workflow-dataset trial start --user <alias>`
- **Do not:** Sit with them and drive every step. Give them the docs and a clear “try these tasks; record feedback when done.”

---

## 2. Choosing the right trial tasks

- **Must try first:** `ops_summarize_reporting`, `ops_next_steps`, `release_demo`. These match the narrow release scope.
- **Nice to try:** `ops_scaffold_status`, console suggestions. Only if they have time.
- **Boundary tasks:** Use to test failure behavior (out-of-scope ask, apply preview only). Explain that these are “see how it fails safely.”
- **Do not** add tasks outside the ops reporting scope for this trial.

---

## 3. Observing without over-directing

- **Strong signal:** User completes a task from the quickstart without you telling them what to click or type.
- **Weak signal:** User says “it worked” after you walked them through every step.
- **Avoid:** Hovering, answering “what should I do next?” with the exact command, or filling in feedback for them.
- **Encourage:** “Use the quickstart; if something is unclear, note it in feedback.” Then step back.

---

## 4. What feedback to look for

- **Outcome:** Did they complete the task, get stuck, or hit an error?
- **Usefulness (1–5):** Do they find the output relevant?
- **Trust (1–5):** Would they consider adopting/applying the suggestion in real work?
- **Confusion/failure points:** Free text is gold. Look for repeated themes across users.
- **Freeform:** Feature requests and “I expected X” help shape M20.

---

## 5. Interpreting weak vs strong signals

- **Strong:** Multiple tasks completed unassisted; usefulness/trust ≥ 3; specific confusion points.
- **Weak:** Single session; all feedback from one guided run; vague “it’s good” or “it’s broken.”
- **Decision:** Prefer “refine internally” if signals are weak or failure rate is high. Prefer “continue trial” or “narrow private pilot” only when you have at least 2–3 sessions with clear, unassisted completion and structured feedback.

---

## 6. When to stop a trial and record a failure

- **Stop and record:** If the user cannot complete setup after following the quickstart, or hits a blocker (e.g. missing graph, missing LLM) that you do not want to fix in this cycle. Record feedback with outcome `failed` and note the blocker.
- **Do not** keep the trial “in progress” indefinitely. End the session, run `workflow-dataset trial summary`, and optionally `workflow-dataset trial aggregate-feedback`.

---

## 7. Deciding if the release is ready for a wider private pilot

Use the aggregated feedback report (`data/local/trials/latest_feedback_report.md`) and the recommendation at the bottom:

- **Refine internally:** Failure rate high, or usefulness/trust low, or no clear “would use this” signal. Do another internal loop before more users.
- **Continue friendly trial:** Some success; need more sessions or more diverse users before expanding.
- **Expand to narrow private pilot:** Multiple unassisted successes, usefulness and trust above threshold, and clear evidence that outputs are adoptable. Then (in a later milestone) add a few more trusted users and slightly broader tasks—still within the narrow scope.

---

## 8. Commands reference

- `workflow-dataset trial start --user <alias>` — start session
- `workflow-dataset trial tasks` — list tasks
- `workflow-dataset trial record-feedback <task_id> --outcome completed --usefulness 4 --trust 3 -f "notes"` — record feedback
- `workflow-dataset trial summary` — write session summary
- `workflow-dataset trial aggregate-feedback` — write latest_feedback_report.md

Console: **F** from Home → Friendly trial (session, tasks, quick feedback, summary).

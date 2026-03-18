# M19 trial-readiness decision (evidence-based)

This document answers the five decision questions for the narrow release. Update it after first real trial sessions and aggregate feedback.

---

## 1. Is the narrow release ready for friendly-user trials now?

**Yes, with the M19 kit.** The narrow release (Operations reporting assistant) has:

- Defined scope and tasks (summarize reporting, scaffold status, next steps).
- Release config and entrypoints (`release verify`, `run`, `demo`).
- A trial kit (overview, quickstart, expectations, boundaries, tasks, troubleshooting).
- Structured feedback capture (local-only), trial CLI, and optional console flow.
- An operator guide so the founder does not over-assist.

**Caveat:** The first trial user should be someone who can follow the quickstart with minimal handholding. If setup (graph, LLM adapter) is not already done, the operator should do a one-time setup or provide a pre-configured environment.

---

## 2. What kind of user should be the first trial user?

- **Profile:** Someone who does recurring reporting or status work (ops) and is willing to try a narrow, suggest-only tool.
- **Mindset:** Expects to read docs and try a few tasks; does not expect a full product or automation of critical paths.
- **Not:** A stakeholder who needs a polished demo, or someone with no ops/reporting context.

---

## 3. What should they be asked to try first?

In order:

1. **Release verify** — confirm setup (graph, adapter if available).
2. **Trial start** — create a session with optional alias.
3. **First task:** Either `workflow-dataset release demo` (3 prompts) or `workflow-dataset release run` (ops trials).
4. **Record feedback** — use `trial record-feedback <task_id>` or the console (F → Record quick feedback) with outcome, usefulness, trust, and optional freeform.
5. **Trial summary** — at end of session run `trial summary`; optionally run `trial aggregate-feedback` to generate the report.

Must-try tasks: `ops_summarize_reporting`, `ops_next_steps`, `release_demo`. Nice-to-try: `ops_scaffold_status`, console suggestions.

---

## 4. What should definitely NOT be included in the trial yet?

- **Out-of-scope workflows:** Spreadsheets, creative/design automation, finance automation, or any domain outside ops reporting.
- **Uncontrolled apply:** Users must not run apply without explicit preview and confirm; trial docs state apply is opt-in and sandbox-first.
- **Production data/critical paths:** Trial should use sandbox or non-critical data only.
- **Promise of support for NOT_YET_SUPPORTED items:** Per docs/NOT_YET_SUPPORTED.md — no promise of full automation, multi-user, or cloud features.

---

## 5. Exact success criteria for M20 (refine vs narrow private pilot)

Use the aggregated feedback report and the following:

- **Choose “more internal refinement”** if:
  - Failure rate (outcome=failed) is high relative to completed, or
  - Average usefulness or trust is below 3, or
  - Fewer than 2 sessions with unassisted task completion, or
  - Recurring confusion/failure points that indicate missing docs or fragile flows.

- **Choose “narrow private pilot expansion”** if:
  - At least 2–3 trial sessions with unassisted completion of must-try tasks,
  - Average usefulness ≥ 3 and trust ≥ 3,
  - Clear evidence that users find outputs adoptable (e.g. freeform says they would use the suggestion),
  - No critical blockers in confusion/failure points.

Update this section with actual numbers after running `trial aggregate-feedback` and reviewing `data/local/trials/latest_feedback_report.md`.

---

## Next milestone after M19

**M20 — Internal refinement or narrow private pilot**

- If criteria above point to refinement: fix friction, improve docs and flows, run another internal/friendly trial before adding users.
- If criteria point to expansion: add a small number of trusted users (narrow private pilot), still within ops reporting scope; do not broaden product scope yet.

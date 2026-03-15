# Trial expectations

What to expect from the product and from the trial process.

---

## What to expect from the product

- **Relevant but sometimes generic answers** — The assistant uses your project and style context. It may still sound generic; we’re not claiming “deep” personalization yet.
- **Suggestions, not execution** — It will suggest next steps and structures. It will **not** run commands or change files without your explicit “apply” confirmation.
- **Sandbox-first** — Generated scaffolds and bundles are written to a sandbox area (e.g. `data/local/generation`, `data/local/bundles`). Your real project folders are not modified unless you run an apply step and confirm.
- **Local only** — No data is sent to the cloud. All processing and storage stay on your machine.
- **Possible failures** — Some commands may fail (e.g. missing adapter, empty graph). Error messages should explain what’s missing. Recording “failure” or “partial” in feedback helps us fix the flow.

---

## What we expect from you

- **Honest feedback** — Tell us what was useful, what was confusing, and what failed. We need both positive and negative feedback.
- **Structured feedback when possible** — Use `trial record-feedback` with ratings (e.g. usefulness 1–5) so we can aggregate across users. Freeform text is also welcome.
- **Stay within scope** — Focus on the ops/reporting tasks we’ve defined. If you try something out of scope (e.g. creative or spreadsheet-heavy), that’s fine to note in feedback, but we may not support it in v1.
- **One session at a time** — Start a trial session with `trial start`, do a set of tasks, record feedback, then run `trial summary`. You can run multiple sessions over time; we’ll use session id to group feedback.

---

## What success looks like for the trial

- You complete at least 2–3 “must try” tasks.
- You record feedback (outcome, usefulness, and optionally confusion/failure points) for each.
- We get a clear signal: either “this is useful enough to try with more users” or “we need to fix X before inviting more people.”

We are **not** measuring growth or engagement. We are measuring **usefulness and friction** so we can decide the next product step.

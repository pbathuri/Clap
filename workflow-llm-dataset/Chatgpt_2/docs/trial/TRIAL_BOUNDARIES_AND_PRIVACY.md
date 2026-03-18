# Trial boundaries and privacy

How we handle your data and what stays local.

---

## Privacy

- **All processing is local** — The app runs on your machine. No telemetry, no analytics, no cloud APIs for the core flow.
- **Feedback is stored locally** — When you run `trial record-feedback`, the feedback is saved under `data/local/trials` (or the configured path) on your machine. It is not automatically sent anywhere.
- **Sharing is your choice** — If you share feedback with the trial operator (e.g. by sending the contents of a feedback file or session summary), that’s your decision. We do not collect it remotely.
- **No account or login** — You use a **trial session id** and optionally a **user alias** (e.g. “user1”) so we can tell sessions apart. No personal account is required.

---

## Boundaries of the trial

- **Scope** — The trial is for the **Operations reporting assistant** narrow release only. We do not support spreadsheet automation, creative packages, or multi-user flows in this trial.
- **No production guarantee** — This is an early trial. We do not promise uptime, speed, or correctness. We do promise to use your feedback to improve.
- **Apply is always opt-in** — The system will never write to your real project paths without an explicit “apply” and your confirmation. If something tries to, that’s a bug; please report it.
- **Safe to stop** — You can stop the trial at any time. Your feedback files remain on your machine unless you delete them.

---

## What we do not do

- We do **not** send your project contents or feedback to our servers.
- We do **not** track which commands you run beyond what’s stored locally for trial summaries (e.g. “tasks attempted” per session).
- We do **not** use your data to train external models; any local model training uses only the data you have in this repo (e.g. corpus and SFT data you’ve built).

If anything in the app appears to violate this (e.g. a network call you didn’t expect), please note it in your feedback and we’ll treat it as a bug.

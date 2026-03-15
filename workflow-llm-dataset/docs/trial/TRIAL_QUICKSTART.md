# Trial quickstart

Get from zero to your first useful output in a few steps.

---

## Prerequisites

- You have the repo and can run commands from the project root (e.g. in a terminal).
- Python/venv is set up (the same one used for the founder demo).
- You have a **small set of real work** to point at: e.g. a folder with a few documents or spreadsheets that represent your reporting or ops work. Empty setup will work but outputs will be generic.

---

## Step 1: Verify release readiness

Run:

```bash
workflow-dataset release verify
```

You should see:

- **Graph: OK** (or a message that setup is needed).
- **Setup dir / Parsed artifacts / Style signals** — at least one OK if you’ve run setup before.
- **LLM adapter: OK** if a trained model is available (otherwise the system will still run with a baseline).

If something is missing, the command will tell you. For a first trial, having the graph and at least one setup path is enough; the adapter is optional but recommended.

---

## Step 2: Start a trial session

Run:

```bash
workflow-dataset trial start
```

This creates a trial session and prints a **session id**. Use this session id when you record feedback later. You can run `workflow-dataset trial tasks` to see the list of trial tasks.

---

## Step 3: Run your first task

Try the first “must try” task: **summarize reporting workflow**.

From the CLI:

```bash
workflow-dataset release run
```

This runs the built-in ops tasks (including “summarize reporting workflow”) and writes results under `data/local/trials`. You can also run a single prompt:

```bash
workflow-dataset llm demo --prompt "Summarize this user's recurring reporting workflow and suggest a weekly status structure."
```

Read the output. Did it feel relevant? Too generic? Broken?

---

## Step 4: Record feedback

After you try a task, record your feedback:

```bash
workflow-dataset trial record-feedback --task-id ops_summarize_reporting --outcome completed --usefulness 3
```

(Adjust outcome and usefulness to match your experience. See `workflow-dataset trial record-feedback --help` for options.)

You can add freeform text:

```bash
workflow-dataset trial record-feedback --task-id ops_summarize_reporting --outcome completed --usefulness 4 --freeform "Output was relevant but a bit generic; would help to see my project names."
```

---

## Step 5: Try more tasks and summarize

- Do 2–3 more tasks from **TRIAL_TASKS.md** (must-try and nice-to-try).
- When you’re done for the day, run:

```bash
workflow-dataset trial summary
```

This writes a **session summary** for your trial so far. Share that summary (or the generated file) with the operator if you’re doing a guided trial.

---

## Optional: Use the console

If you prefer a menu-driven flow:

```bash
workflow-dataset console
```

From the home screen you can:

- **2** — Projects  
- **3** — Suggestions  
- **8** — Chat / explain  
- **R** — Release (scope and commands)  
- **T** — Trials (tasks and report)

Then run the same trial tasks and record feedback via the CLI as above.

---

## What to do if something breaks

See **TROUBLESHOOTING.md**. If the problem isn’t listed, note what you ran and what you saw and share it with the trial operator (e.g. as freeform feedback or in person).

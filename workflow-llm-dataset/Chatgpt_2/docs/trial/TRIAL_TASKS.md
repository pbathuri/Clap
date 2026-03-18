# Trial tasks

Concrete tasks to try during the friendly user trial. Focus on “must try” first; then “nice to try” and “boundary” tasks if you have time.

---

## Must try (do these first)

### 1. Summarize reporting workflow

- **What to do:** Run the release flow so the system summarizes your recurring reporting workflow and suggests a weekly status structure.
- **How:**  
  `workflow-dataset release run`  
  or  
  `workflow-dataset llm demo --prompt "Summarize this user's recurring reporting workflow and suggest a weekly status structure."`
- **Expected:** A short text summary and/or structure suggestion. It may feel generic if you have little setup data.
- **Feedback:** Record with task_id `ops_summarize_reporting`. Rate usefulness (1–5) and note if anything was confusing or wrong.

### 2. Get next-step suggestions

- **What to do:** Ask for next-step recommendations based on your projects and routines.
- **How:**  
  `workflow-dataset llm demo --prompt "Based on my projects and routines, what are sensible next steps?"`  
  Or use the console: **3** Suggestions, or **8** Chat.
- **Expected:** A list or paragraph of suggested next steps. The system does not execute them.
- **Feedback:** Record with task_id `ops_next_steps`. Note whether suggestions felt relevant.

### 3. Run the founder demo (3 prompts)

- **What to do:** Run the same demo the founder would show: three prompts about workflow style, recurring patterns, and reporting structure.
- **How:**  
  `workflow-dataset release demo`
- **Expected:** Three answers printed in the terminal. Optionally run with `--retrieval` to see retrieval-grounded answers.
- **Feedback:** You can record one overall feedback entry for “release demo” or one per prompt. Note which answers were useful and which were too generic.

---

## Nice to try

### 4. Scaffold status report

- **What to do:** Ask the system to scaffold a weekly status report package in your style.
- **How:**  
  `workflow-dataset trials run ops_scaffold_status --mode adapter`
- **Expected:** A text response describing a suggested structure. No file creation unless you use generation/bundle flows separately.
- **Feedback:** task_id `ops_scaffold_status`.

### 5. View suggestions in the console

- **What to do:** Open the operator console and look at Suggestions and Projects.
- **How:**  
  `workflow-dataset console` → **2** Projects, **3** Suggestions.
- **Expected:** Lists of projects and style-aware suggestions. May be empty if setup has no data.
- **Feedback:** Note in freeform whether the console was clear or confusing.

---

## Boundary tests (optional)

### 6. Ask something out of scope

- **What to do:** Ask for something we said we don’t support yet (e.g. “Create a spreadsheet from my data” or “Write a creative brief”).
- **Expected:** The system may still answer, but the answer may be generic or wrong. We want to see how it fails.
- **Feedback:** Record outcome as “partial” or “failed” and describe what you asked and what you got. Task_id can be `boundary_spreadsheet` or `boundary_creative`.

### 7. Run apply preview (no confirm)

- **What to do:** Go as far as apply **preview** (see what would be copied where). Do **not** confirm apply unless you intend to.
- **How:** Use console Apply (6) or `workflow-dataset assist apply-preview` if you have an adoption candidate.
- **Expected:** A diff or plan. No files changed. Confirms that apply is separate and explicit.
- **Feedback:** Note whether the preview was clear and whether you felt safe.

---

## Task IDs for feedback

When recording feedback, use these task_ids so we can aggregate:

| task_id | Description |
|--------|-------------|
| `ops_summarize_reporting` | Summarize reporting workflow + weekly status suggestion |
| `ops_scaffold_status` | Scaffold weekly status report |
| `ops_next_steps` | Next-step recommendations |
| `release_demo` | Full release demo (3 prompts) |
| `boundary_spreadsheet` | Out-of-scope: spreadsheet |
| `boundary_creative` | Out-of-scope: creative |
| `boundary_apply_preview` | Apply preview only |

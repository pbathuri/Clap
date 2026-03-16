# Founder demo flow — Operations reporting assistant (v1)

How to demo the product in a clean, credible way. Pre-demo setup, exact commands, what to show, and where to be honest about limitations.

---

## Grounded vs ungrounded demo

- **Ungrounded (generic):** `release demo` with no retrieval and no task context — outputs are generic. The CLI prints `[Ungrounded: no retrieval or task context; outputs may be generic]`.
- **Grounded by task context:** Pass explicit task-scoped context so the model stays on ops/reporting. Use `--context-file path/to/context.txt` (local file, resolved from project root) and/or `--context-text "weekly ops reporting for project delivery"`. The CLI prints `[Grounded: task context used]`. Context is capped at 2000 characters; local-only.
- **Grounded by retrieval:** Run `setup init` and `setup run`, prepare corpus (`llm prepare-corpus`), and use `release demo --retrieval` when `data/local/llm/corpus/corpus.jsonl` exists. The CLI prints `[Grounded: retrieval context used]`. For each prompt the CLI shows **Retrieval relevance: high | mixed | weak** — use this to recognize weak grounding. When relevance is weak or mixed, the model is instructed to say so and give only a qualified answer.
- **Grounded by both:** Use `--context-file` or `--context-text` together with `--retrieval`. The CLI prints `[Grounded: task context + retrieval]`. If retrieval is weak or mixed, the model is instructed to prioritize the task context and not overstate from retrieved snippets.

**When to use which:** Use `--retrieval` when you have a populated corpus and want answers grounded in it. Use `--context-file` or `--context-text` when you want to pin the demo to a specific ops/reporting scenario without relying on corpus, or to anchor the run when retrieval is often weak/mixed. Use both when you have both and want task context to dominate when retrieval is noisy.

**Evidence files (local-only):** After the run, `data/local/pilot/last_demo_grounding.txt` records `ungrounded` | `task_context_only` | `retrieval_only` | `task_context_and_retrieval` and, when retrieval was used, a second line `retrieval_relevance: weak|mixed|high`. Use these in session notes for pilot evidence.

Retrieval is scoped to reporting, status, blockers, wins, next steps, project updates, and operations; workflow_step, work_context, and task sources are preferred over occupation/industry.

**Output shape (weekly status):** The third demo prompt produces a **send-ready weekly status artifact** (minimal editing to share): Summary (headline), Wins, Blockers, Risks, Next steps. **Blockers:** operational form—*Blocked by X* / *Waiting on Y* / *Needs decision on Z* / *Dependency unresolved: [what]*—then what would unblock; no vague filler. **Risks:** short, concrete operational risks (e.g. schedule, dependency, approval, quality, resource) with one line each; avoid generic “there are risks”. **Next steps:** operational, concrete (who/what/when); avoid generic-only “follow up” unless unsupported. Owner/timing only when context supports it. When context is weak or mixed, the model labels sections as [Well-supported] vs [Uncertain—limited context] or [Inferred—low confidence] for blockers/risks.

**Artifact handoff:** Without `--save-artifact`, the artifact is terminal-only (prompt 3 text). With `--save-artifact`, the weekly status is written to a sandbox under **data/local/workspaces/weekly_status/** as `weekly_status.md` plus a **manifest.json** (grounding, task_context_used, retrieval_used, retrieval_relevance, timestamp). The CLI prints the exact path; no apply is performed—use the existing M8 apply flow to copy to project if desired. Preview with `cat <path>` or list the directory.

---

## Pre-demo setup requirements

- **Config:** `configs/settings.yaml` (and optionally `configs/release_narrow.yaml` as override) with valid setup paths and graph.
- **Setup run at least once:** So that parsed artifacts and style signals exist; graph has projects. If no real data, use a minimal scan root with a few sample files so the graph is non-empty.
- **LLM adapter (recommended):** Full-trained adapter present so `workflow-dataset llm verify` shows adapter OK. If not, demo can still show baseline/placeholder behavior and explain “with adapter you get personalized summaries.”
- **Corpus (optional):** `data/local/llm/corpus/corpus.jsonl` present if you want to show retrieval-grounded answers.
- **Environment:** Repo venv activated (e.g. `. .venv/bin/activate`); run from repo root.

---

## Exact commands / console flows

### 1. Verify release readiness

```bash
workflow-dataset release verify
```

- **Show:** All checks OK (setup, graph, adapter if present, trials). If something is missing, say what “we’d need for a full demo” and continue with what’s available.

### 2. Show local-first and context

```bash
workflow-dataset llm verify
```

- **Show:** Corpus path, SFT, adapter path (or “adapter missing — we’ll show baseline”). Emphasize: everything runs locally; no cloud.

### 3. Run ops workflow trial (one clear task)

```bash
workflow-dataset trials run ops_summarize_reporting --mode adapter
```

- **Show:** Result summary (task_completion, style_match). Open the result JSON or report and show the `model_response` snippet: “Summarize this user’s recurring reporting workflow…”
- **Wow moment:** “This answer is generated by our local model using your project and style context.”

### 4. Demo-suite (curated prompts)

```bash
workflow-dataset llm demo-suite --llm-config configs/llm_training_full.yaml
```

- **Show:** First two prompts (workflow style, recurring patterns). Read the first 2–3 lines of each model output.
- **Optional:** Run again with `--retrieval` and compare: “With retrieval we ground the answer in the corpus.”

### 5. Suggestions (if setup has data)

```bash
workflow-dataset assist suggest --config configs/settings.yaml
```

- **Show:** List of style-aware suggestions (titles and short rationales). “These come from your graph and style signals.”

### 6. Console path (optional)

```bash
workflow-dataset console --config configs/settings.yaml
```

- **Show:** Home → Setup summary (1) or Projects (2) or Suggestions (3). Then L (LLM status) or T (Trials). “One place to see status and run trials.”

### 7. Release report

```bash
workflow-dataset release report
```

- **Show:** `data/local/release/release_readiness_report.md`: scope, supported workflows, evidence, safety, demo readiness.

---

## Artifacts to preload

- **Minimal:** A few files under a scan root (e.g. a markdown readme, a small CSV or Excel) so parsing produces at least one project and style signals.
- **Optional:** Pre-run `workflow-dataset llm prepare-corpus` and `workflow-dataset llm build-sft` and `workflow-dataset llm train --llm-config configs/llm_training_full.yaml` so the full adapter exists and demo uses it.

---

## Prompts to use

- “Summarize this user’s workflow style.”
- “What recurring work patterns are visible?”
- “Summarize this user’s recurring reporting workflow and suggest a weekly status structure.” (trial prompt)

Use these in `llm demo` or `llm demo-suite` or as the trial goal.

---

## Outputs to highlight

- **Model response text** from trials or demo-suite (personalized-ish summary of workflow/reporting).
- **Suggestions list** from `assist suggest` (style-aware, from graph).
- **Release verify** and **release report** (scope, evidence, safety) to show discipline.

---

## Where the “wow” moments are

1. **Local-only:** “Everything you see runs on this machine; no data leaves.”
2. **Personal context:** “This summary is based on your projects and style signals.”
3. **Retrieval (optional):** “We can ground answers in your corpus for more specific references.”
4. **Safe apply:** “We only suggest; apply to your real files only after you confirm.”

---

## Where to be honest about limitations

- **Personalization is mild:** Model often sounds generic; we’re not yet “deeply you.”
- **Retrieval can hurt on metrics:** On eval, retrieval sometimes lowers token overlap; we still use it for qualitative grounding.
- **Narrow scope:** v1 is operations/reporting only; we’re not claiming spreadsheet, creative, or multi-user.
- **No production SLA:** This is a first-draft internal/friendly-user demo, not a shipped product.

Say: “This is the first narrow release — we’re showing what we can do today and what we’re explicitly not doing yet.”

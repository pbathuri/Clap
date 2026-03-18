# First narrow release — Operations reporting assistant

**Based on:** M16 comparison (workflow_inference, knowledge_qa, safety_boundary strongest) and M17 ops workflow trials (ops_summarize_reporting, ops_scaffold_status, ops_next_steps, ops_handoff_bundle).

---

## Target user

- **One person** (founder, operator, or office lead) who runs recurring reporting and status workflows.
- **One device per user**; local-first, no cloud dependency for core flow.
- **Willing to run setup once** (scan roots, parse artifacts, build graph) and then use assistive suggestions and generated scaffolds.

---

## Target workflow category

**Operations / office admin — reporting and status.**

- Recurring reporting workflow summarization.
- Weekly status / report package scaffolding.
- Next-step recommendations from project and routine context.
- Ops handoff bundle from prior patterns (when output adapter is used).

---

## Supported tasks (v1)

| Task | Description | Evidence |
|------|-------------|----------|
| Summarize reporting workflow | Describe user's recurring reporting workflow and suggest a weekly status structure from projects + style signals | M17 ops_summarize_reporting; M16 workflow_inference strong |
| Scaffold status report | Propose a weekly status report package structure in the user's style | M17 ops_scaffold_status |
| Next steps | Recommend next steps based on previous work structure and routines | M17 ops_next_steps; M16 next_step weaker but usable |
| Workflow explanation | Explain what kind of workflow (e.g. operations/data) fits observed patterns (e.g. .csv/.xlsx usage) | M16 workflow_inference, knowledge_qa |

**Model mode for v1:** Full adapter, retrieval optional (M16 showed retrieval can hurt overlap on eval; demo-suite with retrieval still gives grounded answers for qualitative use).

---

## Unsupported tasks (v1)

- **Spreadsheet-heavy** structured workbook creation or population from data (future).
- **Founder** project scaffolding and handoff packages beyond what ops_handoff adapter can do (partial; adapter exists but not primary focus).
- **Creative** brief/storyboard/revision packages (deferred).
- **Multi-user** or **sync/cloud**; v1 is single-user, local-only.
- **Automated execution**; v1 is simulate-first, suggest-only; apply requires explicit user confirmation.

See **docs/NOT_YET_SUPPORTED.md** for full boundary list.

---

## Required setup

- **Config:** `configs/settings.yaml` (or equivalent) with:
  - `paths.graph_store_path` (work graph)
  - `setup` section: setup_dir, style_signals_dir, parsed_artifacts_dir, style_profiles_dir, suggestions_dir, draft_structures_dir
- **Onboarding:** At least one setup session completed (`setup init`, `setup run` or equivalent) so that:
  - Parsed artifacts and style signals exist
  - Graph has projects/nodes
- **LLM (optional but recommended):** Full-trained adapter available so that `llm verify` reports adapter OK; if missing, baseline/placeholder behavior only.

---

## Required data sources

- **Graph:** Work graph (from observation/setup) with projects and nodes.
- **Parsed artifacts:** From setup scan (document/tabular/creative etc. as configured).
- **Style signals:** Naming, export, revision patterns from setup.
- **Corpus (optional):** `data/local/llm/corpus/corpus.jsonl` for retrieval-grounded prompts when retrieval is enabled.

---

## Expected outputs

- **Suggestions:** Style-aware suggestions (e.g. “treat this project as ops workflow”) from `assist suggest`.
- **Explanations:** Text answers from the assistant (workflow type, next steps, reporting summary) via demo or console chat.
- **Scaffolds / bundles:** When using generation + output adapters: ops handoff bundle, status report scaffold, under sandbox (e.g. `data/local/generation`, `data/local/bundles`). No writes to real project paths without explicit apply.
- **Adoption candidates:** Selected outputs can be turned into adoption candidates for apply-preview and apply-confirm.

---

## Safety boundaries

- **No uncontrolled writes:** All generated/bundled outputs go to sandbox dirs (generation workspace, bundle root). Writes to user’s real filesystem only via **apply** with confirmation.
- **Simulate-first:** Agent suggests and explains; it does not execute without approval.
- **Local-only:** No cloud APIs; no telemetry; no external calls except optional model download (e.g. Hugging Face) for LLM.

---

## What “success” means for this release

- **Internal founder demo:** A founder can run the narrow-release flow (release verify → release demo or release run) and show:
  - Local setup and graph
  - Retrieval-grounded or adapter-generated explanations for reporting/workflow
  - A generated scaffold or bundle in the sandbox
  - Apply preview and optional apply confirmation
- **Friendly-user trial:** A single friendly user can repeat the same flow with their own setup and see coherent, relevant suggestions and one clear “before/after” moment (e.g. “here’s your reporting workflow summary” or “here’s a status scaffold for your style”).
- **Truthful boundary:** We do not claim support for creative, spreadsheet, or multi-user flows in v1; we document and show only what the evidence supports.
